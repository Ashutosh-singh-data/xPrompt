import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd

from app.engine.schemas import (
    InvestigationPlan,
    PlannedTask,
    PlannedHypothesis,
    ExecutionSummary,
    TaskExecutionResult,
)
from app.engine.validator import PlanValidator, plan_validator
from app.engine.tools.registry import tool_registry, ToolRegistry
from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.task import InvestigationTask, TaskStatus

logger = logging.getLogger("consultos.engine.replanner")

DEFAULT_MAX_REPLAN_ITERATIONS = 2
DEFAULT_MAX_TOTAL_TASKS = 15


def normalize_task_signature(tool_name: str, parameters: Dict[str, Any]) -> str:
    """Create a canonical deterministic JSON string signature of a task specification."""
    try:
        clean_params = {}
        for k, v in sorted(parameters.items()):
            if isinstance(v, (list, tuple)):
                clean_params[k] = sorted([str(item) for item in v])
            else:
                clean_params[k] = v
        return f"{tool_name}::{json.dumps(clean_params, sort_keys=True)}"
    except Exception:
        return f"{tool_name}::{str(parameters)}"


class ReplanEvaluation:
    """Outcome of a replanning evaluation."""

    def __init__(
        self,
        needed: bool,
        trigger: Optional[str] = None,
        unresolved_question: Optional[str] = None,
        reason: Optional[str] = None,
        follow_up_tasks: Optional[List[PlannedTask]] = None,
    ):
        self.needed = needed
        self.trigger = trigger
        self.unresolved_question = unresolved_question
        self.reason = reason
        self.follow_up_tasks = follow_up_tasks or []


class DynamicReplanner:
    """Inspects investigation state, evidence, and task executions to formulate targeted follow-up tasks.

    Enforces:
    - Bounded replanning attempts and total task caps.
    - Non-duplication of equivalent tasks.
    - Dependency cycle prevention and schema validation.
    - Preservation of prior results when no valid next step exists.
    """

    def __init__(
        self,
        validator: Optional[PlanValidator] = None,
        registry: Optional[ToolRegistry] = None,
        max_replan_iterations: int = DEFAULT_MAX_REPLAN_ITERATIONS,
        max_total_tasks: int = DEFAULT_MAX_TOTAL_TASKS,
    ):
        self.validator = validator or plan_validator
        self.registry = registry or tool_registry
        self.max_replan_iterations = max_replan_iterations
        self.max_total_tasks = max_total_tasks

    def evaluate_and_replan(
        self,
        plan: InvestigationPlan,
        completed_results: Dict[str, TaskExecutionResult],
        evidence_list: List[Evidence],
        hypotheses: List[Hypothesis],
        df: pd.DataFrame,
        current_replan_iteration: int = 0,
    ) -> ReplanEvaluation:
        """Evaluate current investigation outcomes and generate valid follow-up tasks if needed."""
        # 1. Enforce iteration and task caps
        if current_replan_iteration >= self.max_replan_iterations:
            logger.info(
                f"Replanning skipped: reached maximum replan iteration limit ({self.max_replan_iterations})."
            )
            return ReplanEvaluation(
                needed=False,
                trigger="limit_reached",
                unresolved_question=None,
                reason=f"Exceeded maximum replan limit of {self.max_replan_iterations} iterations.",
            )

        if len(plan.tasks) >= self.max_total_tasks:
            logger.info(
                f"Replanning skipped: reached maximum total task limit ({self.max_total_tasks})."
            )
            return ReplanEvaluation(
                needed=False,
                trigger="limit_reached",
                unresolved_question=None,
                reason=f"Exceeded maximum task count limit of {self.max_total_tasks} tasks.",
            )

        # 2. Inspect existing tasks to build signature set for deduplication
        existing_signatures: Set[str] = {
            normalize_task_signature(t.tool_name, t.parameters) for t in plan.tasks
        }
        existing_task_ids: Set[str] = {t.id for t in plan.tasks}

        # 3. Identify successful tasks to act as valid prerequisites
        successful_task_ids = [
            t_id for t_id, res in completed_results.items() if res.status == "completed"
        ]
        base_prereq_id = successful_task_ids[0] if successful_task_ids else None

        # Determine available columns, metric columns, and dimension columns
        available_columns = list(df.columns)
        metric_cols = [c for c in available_columns if pd.api.types.is_numeric_dtype(df[c])]
        dimension_cols = [c for c in available_columns if c not in metric_cols]

        candidate_tasks: List[PlannedTask] = []
        trigger: Optional[str] = None
        unresolved_question: Optional[str] = None
        reason: Optional[str] = None

        # Check Trigger 1: A task failed
        failed_tasks = [
            t for t in plan.tasks if completed_results.get(t.id) and completed_results[t.id].status == "failed"
        ]
        if failed_tasks:
            f_task = failed_tasks[0]
            f_res = completed_results[f_task.id]
            trigger = "task_failure"
            unresolved_question = (
                f"Analytical task '{f_task.title}' failed ({f_res.error}). "
                f"How can we extract compensatory insights using alternative analytical dimensions?"
            )
            reason = f"Primary task '{f_task.id}' failed; attempting fallback analytical procedure."

            # If timeseries analyzer failed, fallback to grouped aggregation or overall metrics
            if f_task.tool_name == "timeseries_analyzer" and metric_cols and dimension_cols:
                fallback_task_id = f"task_replan_{len(plan.tasks) + 1}"
                dim = dimension_cols[0]
                met = metric_cols[0]
                params = {
                    "group_by": [dim],
                    "metric_column": met,
                    "agg_funcs": ["sum", "mean", "count"],
                }
                sig = normalize_task_signature("grouped_aggregator", params)
                if sig not in existing_signatures:
                    candidate_tasks.append(
                        PlannedTask(
                            id=fallback_task_id,
                            title=f"Fallback: Grouped analysis of {met} by {dim}",
                            description=f"Compensatory grouped analysis following time-series failure.",
                            task_type="analysis",
                            tool_name="grouped_aggregator",
                            parameters=params,
                            dependency_ids=[base_prereq_id] if base_prereq_id else [],
                            hypothesis_id=f_task.hypothesis_id,
                        )
                    )

            # If grouped aggregation failed on one dimension, try alternative dimension
            elif f_task.tool_name == "grouped_aggregator" and len(dimension_cols) > 1 and metric_cols:
                for alt_dim in dimension_cols:
                    params = {
                        "group_by": [alt_dim],
                        "metric_column": metric_cols[0],
                        "agg_funcs": ["sum", "mean", "count"],
                    }
                    sig = normalize_task_signature("grouped_aggregator", params)
                    if sig not in existing_signatures:
                        candidate_tasks.append(
                            PlannedTask(
                                id=f"task_replan_{len(plan.tasks) + 1}",
                                title=f"Alternative breakdown of {metric_cols[0]} by {alt_dim}",
                                description=f"Secondary dimensional breakdown following primary aggregation failure.",
                                task_type="analysis",
                                tool_name="grouped_aggregator",
                                parameters=params,
                                dependency_ids=[base_prereq_id] if base_prereq_id else [],
                                hypothesis_id=f_task.hypothesis_id,
                            )
                        )
                        break

        # Check Trigger 2: Data quality issue detected
        if not candidate_tasks:
            data_val_res = next(
                (
                    completed_results[t.id].result
                    for t in plan.tasks
                    if t.tool_name == "data_validator"
                    and completed_results.get(t.id)
                    and completed_results[t.id].status == "completed"
                ),
                None,
            )
            if data_val_res and isinstance(data_val_res, dict) and not data_val_res.get("is_valid", True):
                issues = data_val_res.get("issues", [])
                trigger = "data_quality_issue"
                unresolved_question = (
                    f"Data quality constraints violation detected ({len(issues)} issues). "
                    f"How do metric distributions behave when computing robust summary statistics?"
                )
                reason = "Data quality issues detected; computing overall robust summary metrics."

                if metric_cols:
                    params = {
                        "metric_column": metric_cols[0],
                        "agg_funcs": ["mean", "median", "min", "max", "std"],
                    }
                    sig = normalize_task_signature("grouped_aggregator", params)
                    if sig not in existing_signatures:
                        candidate_tasks.append(
                            PlannedTask(
                                id=f"task_replan_{len(plan.tasks) + 1}",
                                title=f"Compute robust distribution statistics for {metric_cols[0]}",
                                description="Calculate mean, median, standard deviation to assess data quality skewness.",
                                task_type="analysis",
                                tool_name="grouped_aggregator",
                                parameters=params,
                                dependency_ids=[base_prereq_id] if base_prereq_id else [],
                                hypothesis_id=None,
                            )
                        )

        # Check Trigger 3: Inconclusive hypothesis
        if not candidate_tasks:
            inconclusive_hyps = [
                h for h in hypotheses if h.status == HypothesisStatus.INCONCLUSIVE.value
            ]
            if inconclusive_hyps:
                inc_hyp = inconclusive_hyps[0]
                trigger = "hypothesis_inconclusive"
                unresolved_question = (
                    f"Hypothesis '{inc_hyp.statement}' remains inconclusive. "
                    f"Are there unexplored categorical dimensions or statistical facets?"
                )
                reason = f"Hypothesis '{inc_hyp.id}' is inconclusive; adding targeted analytical coverage."

                # Find unanalyzed dimensions
                analyzed_dims: Set[str] = set()
                for t in plan.tasks:
                    if t.tool_name == "grouped_aggregator":
                        gb = t.parameters.get("group_by", [])
                        if isinstance(gb, list):
                            analyzed_dims.update(gb)
                        elif isinstance(gb, str):
                            analyzed_dims.add(gb)

                remaining_dims = [d for d in dimension_cols if d not in analyzed_dims]
                if remaining_dims and metric_cols:
                    next_dim = remaining_dims[0]
                    params = {
                        "group_by": [next_dim],
                        "metric_column": metric_cols[0],
                        "agg_funcs": ["sum", "mean", "count"],
                    }
                    sig = normalize_task_signature("grouped_aggregator", params)
                    if sig not in existing_signatures:
                        candidate_tasks.append(
                            PlannedTask(
                                id=f"task_replan_{len(plan.tasks) + 1}",
                                title=f"Explore dimensional concentration across {next_dim}",
                                description=f"Secondary dimensional investigation to test hypothesis '{inc_hyp.id}'.",
                                task_type="analysis",
                                tool_name="grouped_aggregator",
                                parameters=params,
                                dependency_ids=[base_prereq_id] if base_prereq_id else [],
                                hypothesis_id=inc_hyp.id,
                            )
                        )

        # Check Trigger 4: Evidence insufficiency
        if not candidate_tasks:
            verified_count = sum(
                1 for e in evidence_list if e.verification_status == EvidenceVerificationStatus.VERIFIED.value
            )
            if verified_count == 0 and len(successful_task_ids) > 0:
                trigger = "insufficient_evidence"
                unresolved_question = "All generated evidence was inconclusive or rejected; baseline statistical context needed."
                reason = "Evidence is insufficient; generating baseline summary task."

                if metric_cols:
                    params = {
                        "metric_column": metric_cols[0],
                        "agg_funcs": ["sum", "mean", "count"],
                    }
                    sig = normalize_task_signature("grouped_aggregator", params)
                    if sig not in existing_signatures:
                        candidate_tasks.append(
                            PlannedTask(
                                id=f"task_replan_{len(plan.tasks) + 1}",
                                title=f"Establish overall baseline metrics for {metric_cols[0]}",
                                description="Calculate overall totals and averages to produce verified baseline evidence.",
                                task_type="analysis",
                                tool_name="grouped_aggregator",
                                parameters=params,
                                dependency_ids=[base_prereq_id] if base_prereq_id else [],
                                hypothesis_id=None,
                            )
                        )

        # 4. If no valid tasks were formulated, replanning is not needed or feasible
        if not candidate_tasks:
            logger.info("No viable, non-duplicate follow-up tasks could be formulated.")
            return ReplanEvaluation(
                needed=False,
                trigger=trigger,
                unresolved_question=unresolved_question,
                reason="No viable, non-duplicate follow-up analytical tasks could be generated.",
            )

        # 5. Validate proposed follow-up tasks
        augmented_plan = InvestigationPlan(
            plan_id=plan.plan_id,
            business_question=plan.business_question,
            dataset_name=plan.dataset_name,
            hypotheses=plan.hypotheses,
            tasks=plan.tasks + candidate_tasks,
        )

        validation = self.validator.validate(
            augmented_plan,
            available_columns=available_columns,
        )

        if not validation.is_valid:
            logger.warning(
                f"Proposed replanning tasks failed validation: {validation.errors}"
            )
            return ReplanEvaluation(
                needed=False,
                trigger=trigger,
                unresolved_question=unresolved_question,
                reason=f"Candidate tasks failed plan validation: {'; '.join(validation.errors)}",
            )

        logger.info(
            f"Replanning approved: {len(candidate_tasks)} new follow-up tasks generated for trigger '{trigger}'."
        )
        return ReplanEvaluation(
            needed=True,
            trigger=trigger,
            unresolved_question=unresolved_question,
            reason=reason,
            follow_up_tasks=candidate_tasks,
        )


dynamic_replanner = DynamicReplanner()
