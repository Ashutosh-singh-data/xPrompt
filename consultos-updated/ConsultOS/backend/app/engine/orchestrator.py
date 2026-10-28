import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
import pandas as pd
from app.engine.schemas import (
    InvestigationPlan,
    PlannedTask,
    ExecutionSummary,
    TaskExecutionResult,
)
from app.engine.graph import DependencyGraph
from app.engine.executor import TaskExecutor, task_executor
from app.engine.validator import PlanValidator, plan_validator

logger = logging.getLogger("consultos.engine.orchestrator")


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvestigationOrchestrator:
    """Coordinates the execution of an analytical investigation plan using DAG dependency resolution."""

    def __init__(
        self,
        executor: Optional[TaskExecutor] = None,
        validator: Optional[PlanValidator] = None,
    ):
        self.executor = executor or task_executor
        self.validator = validator or plan_validator

    def run(
        self,
        plan: InvestigationPlan,
        data: Any,
        investigation_id: Optional[str] = None,
    ) -> ExecutionSummary:
        """Execute all tasks in the plan in dependency order.

        Continues independent tasks if a branch fails, and blocks dependent tasks.
        """
        start_dt = get_utc_now()
        start_time = time.perf_counter()

        # Convert input data to pandas DataFrame
        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported data format for execution: {type(data)}")

        # Validate plan before execution
        val_result = self.validator.validate(plan, available_columns=list(df.columns))
        if not val_result.is_valid:
            duration_ms = (time.perf_counter() - start_time) * 1000
            end_dt = get_utc_now()
            # Return an execution summary reflecting the validation failure
            failed_results = {
                t.id: TaskExecutionResult(
                    task_id=t.id,
                    status="failed",
                    attempts=0,
                    error=f"Plan validation failed: {'; '.join(val_result.errors)}",
                )
                for t in plan.tasks
            }
            return ExecutionSummary(
                plan_id=plan.plan_id,
                investigation_id=investigation_id,
                total_tasks=len(plan.tasks),
                completed_tasks=0,
                failed_tasks=len(plan.tasks),
                blocked_tasks=0,
                task_results=failed_results,
                generated_evidence=[],
                start_time=start_dt,
                end_time=end_dt,
                duration_ms=round(duration_ms, 2),
            )

        # Build Dependency Graph
        graph = DependencyGraph()
        task_map: Dict[str, PlannedTask] = {}
        for task in plan.tasks:
            task_map[task.id] = task
            graph.add_task(task.id, task.dependency_ids)

        completed_task_ids: Set[str] = set()
        failed_task_ids: Set[str] = set()
        blocked_task_ids: Set[str] = set()
        processed_task_ids: Set[str] = set()

        task_results: Dict[str, TaskExecutionResult] = {}
        generated_evidence: List[Dict[str, Any]] = []

        logger.info(f"Starting orchestration for plan '{plan.plan_id}' with {len(plan.tasks)} tasks.")

        # Main orchestration loop
        while len(processed_task_ids) < len(plan.tasks):
            # 1. Block tasks whose prerequisites have failed
            new_blocked = graph.get_blocked_tasks(failed_task_ids) - processed_task_ids
            for b_id in sorted(new_blocked):
                logger.warning(f"Blocking task '{b_id}' due to upstream prerequisite failure.")
                task_results[b_id] = TaskExecutionResult(
                    task_id=b_id,
                    status="blocked",
                    attempts=0,
                    error="Upstream dependency failed.",
                )
                blocked_task_ids.add(b_id)
                processed_task_ids.add(b_id)

            # 2. Find ready tasks (all prereqs completed successfully)
            ready_ids = graph.get_ready_tasks(
                completed_task_ids=completed_task_ids,
                processed_or_active_ids=processed_task_ids,
            )

            if not ready_ids:
                # No tasks are ready and not all are processed: remaining must be blocked or unschedulable
                remaining = set(task_map.keys()) - processed_task_ids
                for rem_id in sorted(remaining):
                    task_results[rem_id] = TaskExecutionResult(
                        task_id=rem_id,
                        status="blocked",
                        attempts=0,
                        error="Prerequisites could not be satisfied.",
                    )
                    blocked_task_ids.add(rem_id)
                    processed_task_ids.add(rem_id)
                break

            # 3. Execute the next ready task in deterministic order
            current_id = ready_ids[0]
            current_task = task_map[current_id]
            logger.info(f"Executing task '{current_id}' ({current_task.tool_name})...")

            result = self.executor.execute_task(
                task=current_task,
                df=df,
                completed_results=task_results,
            )
            task_results[current_id] = result
            processed_task_ids.add(current_id)

            if result.status == "completed":
                completed_task_ids.add(current_id)
                # Extract evidence from successful analytical execution
                evidence_items = self._extract_evidence(
                    current_task, result.result, plan
                )
                generated_evidence.extend(evidence_items)
            else:
                failed_task_ids.add(current_id)

        duration_ms = (time.perf_counter() - start_time) * 1000
        end_dt = get_utc_now()

        logger.info(
            f"Plan '{plan.plan_id}' execution complete: "
            f"{len(completed_task_ids)} completed, {len(failed_task_ids)} failed, "
            f"{len(blocked_task_ids)} blocked in {duration_ms:.2f}ms."
        )

        return ExecutionSummary(
            plan_id=plan.plan_id,
            investigation_id=investigation_id,
            total_tasks=len(plan.tasks),
            completed_tasks=len(completed_task_ids),
            failed_tasks=len(failed_task_ids),
            blocked_tasks=len(blocked_task_ids),
            task_results=task_results,
            generated_evidence=generated_evidence,
            start_time=start_dt,
            end_time=end_dt,
            duration_ms=round(duration_ms, 2),
        )

    def _extract_evidence(
        self,
        task: PlannedTask,
        result_data: Any,
        plan: InvestigationPlan,
    ) -> List[Dict[str, Any]]:
        """Extract structured, verified evidence facts from tool execution results."""
        evidence: List[Dict[str, Any]] = []
        if not isinstance(result_data, dict):
            return evidence

        # Profiling findings
        if task.tool_name == "dataset_profiler":
            row_count = result_data.get("row_count", 0)
            col_count = result_data.get("column_count", 0)
            dup_count = result_data.get("duplicate_rows", 0)
            finding = (
                f"Dataset contains {row_count} records across {col_count} columns with "
                f"{dup_count} duplicate rows."
            )
            evidence.append({
                "task_id": task.id,
                "source_type": "profiling_tool",
                "source_reference": f"tool://{task.tool_name}",
                "finding": finding,
                "supporting_data": {
                    "row_count": row_count,
                    "column_count": col_count,
                    "duplicate_rows": dup_count,
                },
            })

        # Validation findings
        elif task.tool_name == "data_validator":
            issues = result_data.get("issues", [])
            is_valid = result_data.get("is_valid", True)
            finding = (
                f"Data quality check passed with 0 critical issues."
                if is_valid
                else f"Data quality check detected {len(issues)} issues in data constraints."
            )
            evidence.append({
                "task_id": task.id,
                "source_type": "validation_tool",
                "source_reference": f"tool://{task.tool_name}",
                "finding": finding,
                "supporting_data": {"issues": issues, "is_valid": is_valid},
            })

        # Aggregation findings
        elif task.tool_name == "grouped_aggregator":
            groups = result_data.get("groups", [])
            grouped_by = result_data.get("grouped_by", [])
            if groups and grouped_by:
                # Top driver
                top_group = groups[0]
                first_dim = grouped_by[0]
                dim_val = top_group.get(first_dim)
                finding = f"Primary segment '{dim_val}' for dimension '{first_dim}' leads metric volume."
                evidence.append({
                    "task_id": task.id,
                    "source_type": "aggregation_tool",
                    "source_reference": f"tool://{task.tool_name}",
                    "finding": finding,
                    "supporting_data": {"top_group": top_group, "total_groups": len(groups)},
                })

        # Time-series findings
        elif task.tool_name == "timeseries_analyzer":
            trend = result_data.get("trend_direction", "unknown")
            overall_pct = result_data.get("overall_change_pct", 0.0)
            min_period = result_data.get("min_period")
            max_period = result_data.get("max_period")
            finding = (
                f"Time-series trend observed is '{trend}' with overall change of {overall_pct}%. "
                f"Peak occurred on {max_period.get('period') if max_period else 'N/A'}, "
                f"lowest point on {min_period.get('period') if min_period else 'N/A'}."
            )
            evidence.append({
                "task_id": task.id,
                "source_type": "timeseries_tool",
                "source_reference": f"tool://{task.tool_name}",
                "finding": finding,
                "supporting_data": {
                    "trend_direction": trend,
                    "overall_change_pct": overall_pct,
                    "min_period": min_period,
                    "max_period": max_period,
                },
            })

        return evidence


investigation_orchestrator = InvestigationOrchestrator()
