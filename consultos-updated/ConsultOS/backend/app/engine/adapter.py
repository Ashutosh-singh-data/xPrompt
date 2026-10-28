import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from app.models.investigation import Investigation, InvestigationStatus
from app.models.task import InvestigationTask, TaskStatus
from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence
from app.models.event import InvestigationEvent
from app.models.report import FinalReport
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.event_repository import EventRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.core.exceptions import InvestigationNotFoundException
from app.engine.schemas import InvestigationPlan, ExecutionSummary, PlannedTask, TaskExecutionResult
from app.engine.orchestrator import InvestigationOrchestrator, investigation_orchestrator
from app.engine.replanner import DynamicReplanner, dynamic_replanner
from app.services.evidence_verification_service import EvidenceVerificationService
from app.services.hypothesis_evaluation_service import HypothesisEvaluationService
from app.services.report_service import ReportService

logger = logging.getLogger("consultos.engine.adapter")


class InvestigationEngineAdapter:
    """Adapter integrating the analytical planning, execution, verification, and recovery systems with persistence."""

    def __init__(
        self,
        orchestrator: Optional[InvestigationOrchestrator] = None,
        replanner: Optional[DynamicReplanner] = None,
    ):
        self.orchestrator = orchestrator or investigation_orchestrator
        self.replanner = replanner or dynamic_replanner

    def persist_plan(
        self,
        investigation_id: str,
        plan: InvestigationPlan,
        db: Session,
    ) -> Tuple[Investigation, List[InvestigationTask]]:
        """Persist generated hypotheses, planned tasks, and dependencies into the database."""
        inv_repo = InvestigationRepository(db)
        task_repo = TaskRepository(db)
        event_repo = EventRepository(db)

        investigation = inv_repo.get_by_id(investigation_id)
        if not investigation:
            raise InvestigationNotFoundException(investigation_id)

        try:
            # Map planned hypotheses to database models
            hyp_db_map: Dict[str, Hypothesis] = {}
            for hyp in plan.hypotheses:
                db_hyp = Hypothesis(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation_id,
                    statement=hyp.statement,
                    status=HypothesisStatus.PROPOSED.value,
                    confidence=0.5,
                )
                db.add(db_hyp)
                hyp_db_map[hyp.id] = db_hyp

            # Map planned tasks to database models
            task_db_map: Dict[str, InvestigationTask] = {}
            for task in plan.tasks:
                db_task = InvestigationTask(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation_id,
                    title=task.title,
                    description=task.description,
                    task_type=task.task_type,
                    status=TaskStatus.PENDING.value,
                    attempts=0,
                )
                db.add(db_task)
                task_db_map[task.id] = db_task

            db.flush()

            # Record task dependencies using database task IDs
            for task in plan.tasks:
                db_task = task_db_map[task.id]
                for dep_id in task.dependency_ids:
                    if dep_id in task_db_map:
                        prereq_task = task_db_map[dep_id]
                        task_repo.add_dependency(
                            task_id=db_task.id,
                            depends_on_task_id=prereq_task.id,
                        )

            # Update investigation state
            investigation.current_plan_version += 1
            investigation.status = InvestigationStatus.QUEUED.value

            # Persist plan event
            event = InvestigationEvent(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                event_type="plan_generated",
                details={
                    "plan_id": plan.plan_id,
                    "hypotheses_count": len(plan.hypotheses),
                    "tasks_count": len(plan.tasks),
                },
            )
            event_repo.create(event)

            db.commit()
            db.refresh(investigation)
            logger.info(
                f"Persisted plan for investigation '{investigation_id}': "
                f"{len(plan.tasks)} tasks, {len(plan.hypotheses)} hypotheses."
            )
            return investigation, list(task_db_map.values())

        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to persist investigation plan: {exc}", exc_info=True)
            raise

    def execute_and_persist(
        self,
        investigation_id: str,
        plan: InvestigationPlan,
        data: Any,
        db: Session,
        max_replan_iterations: int = 2,
    ) -> ExecutionSummary:
        """Execute an investigation plan against data with bounded recovery, verification, replanning, and report generation."""
        inv_repo = InvestigationRepository(db)
        event_repo = EventRepository(db)
        evidence_repo = EvidenceRepository(db)

        investigation = inv_repo.get_by_id(investigation_id)
        if not investigation:
            raise InvestigationNotFoundException(investigation_id)

        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)

        # 1. First ensure initial plan is persisted if tasks do not yet exist
        tasks_in_db = (
            db.query(InvestigationTask)
            .filter(InvestigationTask.investigation_id == investigation_id)
            .all()
        )

        plan_task_to_db_task: Dict[str, InvestigationTask] = {}
        if not tasks_in_db:
            _, db_tasks = self.persist_plan(investigation_id, plan, db)
            for pt, dt in zip(plan.tasks, db_tasks):
                plan_task_to_db_task[pt.id] = dt
        else:
            for i, pt in enumerate(plan.tasks):
                if i < len(tasks_in_db):
                    plan_task_to_db_task[pt.id] = tasks_in_db[i]
                else:
                    new_dt = InvestigationTask(
                        id=str(uuid.uuid4()),
                        investigation_id=investigation_id,
                        title=pt.title,
                        description=pt.description,
                        task_type=pt.task_type,
                        status=TaskStatus.PENDING.value,
                    )
                    db.add(new_dt)
                    db.flush()
                    plan_task_to_db_task[pt.id] = new_dt

        # 2. Transition status to running
        investigation.status = InvestigationStatus.RUNNING.value
        start_event = InvestigationEvent(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            event_type="investigation_execution_started",
            details={"plan_id": plan.plan_id},
        )
        event_repo.create(start_event)
        db.commit()

        # 3. Execute initial plan via Orchestrator
        summary = self.orchestrator.run(
            plan=plan,
            data=df,
            investigation_id=investigation_id,
        )

        # 4. Persist task execution outcomes & check recovery attempts
        try:
            for plan_task_id, task_res in summary.task_results.items():
                db_task = plan_task_to_db_task.get(plan_task_id)
                if db_task:
                    db_task.status = task_res.status
                    db_task.attempts = max(db_task.attempts, task_res.attempts)
                    db_task.result = task_res.result
                    db_task.error = task_res.error

                    # Log recovery attempt event if task was retried
                    if task_res.recovery_attempts:
                        rec_event = InvestigationEvent(
                            id=str(uuid.uuid4()),
                            investigation_id=investigation_id,
                            task_id=db_task.id,
                            event_type="recovery_attempted",
                            details={
                                "task_id": plan_task_id,
                                "attempts_count": len(task_res.recovery_attempts),
                                "history": task_res.recovery_attempts,
                            },
                        )
                        event_repo.create(rec_event)

                    # Persist task completion/failure event
                    t_event = InvestigationEvent(
                        id=str(uuid.uuid4()),
                        investigation_id=investigation_id,
                        task_id=db_task.id,
                        event_type=f"task_{task_res.status}",
                        details={
                            "task_id": plan_task_id,
                            "execution_time_ms": task_res.execution_time_ms,
                            "attempts": task_res.attempts,
                            "error": task_res.error,
                        },
                    )
                    event_repo.create(t_event)

            # Persist extracted evidence
            for ev_item in summary.generated_evidence:
                plan_task_id = ev_item.get("task_id")
                db_task = plan_task_to_db_task.get(plan_task_id) if plan_task_id else None

                evidence = Evidence(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation_id,
                    task_id=db_task.id if db_task else None,
                    source_type=ev_item.get("source_type", "analytical_tool"),
                    source_reference=ev_item.get("source_reference", "consultos_engine"),
                    finding=ev_item.get("finding", "Analytical finding"),
                    supporting_data=ev_item.get("supporting_data"),
                )
                evidence_repo.create(evidence)

            db.commit()

            # 5. Evidence Verification
            ver_service = EvidenceVerificationService(db)
            verified_ev_list = ver_service.verify_investigation_evidence(investigation_id)

            # 6. Hypothesis Evaluation
            hyp_service = HypothesisEvaluationService(db)
            evaluated_hyps = hyp_service.evaluate_investigation_hypotheses(investigation_id)

            # 7. Check Dynamic Replanning
            replan_iter = 0
            current_plan = plan
            while replan_iter < max_replan_iterations:
                replan_eval = self.replanner.evaluate_and_replan(
                    plan=current_plan,
                    completed_results=summary.task_results,
                    evidence_list=verified_ev_list,
                    hypotheses=evaluated_hyps,
                    df=df,
                    current_replan_iteration=replan_iter,
                )

                if not replan_eval.needed:
                    break

                replan_iter += 1
                investigation.status = InvestigationStatus.REPLANNING.value
                investigation.current_plan_version += 1

                # Record replanning initiated event
                replan_event = InvestigationEvent(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation_id,
                    event_type="replanning_initiated",
                    details={
                        "replan_iteration": replan_iter,
                        "trigger": replan_eval.trigger,
                        "unresolved_question": replan_eval.unresolved_question,
                        "reason": replan_eval.reason,
                        "new_tasks_count": len(replan_eval.follow_up_tasks),
                    },
                )
                event_repo.create(replan_event)

                # Persist follow-up tasks to db
                new_db_tasks: Dict[str, InvestigationTask] = {}
                for pt in replan_eval.follow_up_tasks:
                    db_t = InvestigationTask(
                        id=str(uuid.uuid4()),
                        investigation_id=investigation_id,
                        title=pt.title,
                        description=pt.description,
                        task_type=pt.task_type,
                        status=TaskStatus.PENDING.value,
                    )
                    db.add(db_t)
                    new_db_tasks[pt.id] = db_t
                    plan_task_to_db_task[pt.id] = db_t

                db.flush()

                # Add dependencies
                for pt in replan_eval.follow_up_tasks:
                    db_t = new_db_tasks[pt.id]
                    for dep_id in pt.dependency_ids:
                        if dep_id in plan_task_to_db_task:
                            prereq_task = plan_task_to_db_task[dep_id]
                            task_repo = TaskRepository(db)
                            task_repo.add_dependency(
                                task_id=db_t.id,
                                depends_on_task_id=prereq_task.id,
                            )

                # Record follow_up_tasks_created event
                follow_up_event = InvestigationEvent(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation_id,
                    event_type="follow_up_tasks_created",
                    details={
                        "task_ids": [t.id for t in replan_eval.follow_up_tasks],
                        "task_titles": [t.title for t in replan_eval.follow_up_tasks],
                    },
                )
                event_repo.create(follow_up_event)
                db.commit()

                # Augment plan and execute follow-up tasks
                current_plan = InvestigationPlan(
                    plan_id=current_plan.plan_id,
                    business_question=current_plan.business_question,
                    dataset_name=current_plan.dataset_name,
                    hypotheses=current_plan.hypotheses,
                    tasks=current_plan.tasks + replan_eval.follow_up_tasks,
                )

                # Run follow-up execution
                replan_summary = self.orchestrator.run(
                    plan=current_plan,
                    data=df,
                    investigation_id=investigation_id,
                )
                summary = replan_summary

                # Update database for follow-up tasks
                for plan_task_id, task_res in replan_summary.task_results.items():
                    db_t = plan_task_to_db_task.get(plan_task_id)
                    if db_t:
                        db_t.status = task_res.status
                        db_t.attempts = max(db_t.attempts, task_res.attempts)
                        db_t.result = task_res.result
                        db_t.error = task_res.error

                # Persist new evidence
                for ev_item in replan_summary.generated_evidence:
                    plan_task_id = ev_item.get("task_id")
                    # Check if this evidence was already created
                    existing_ev = (
                        db.query(Evidence)
                        .filter(
                            Evidence.investigation_id == investigation_id,
                            Evidence.finding == ev_item.get("finding"),
                        )
                        .first()
                    )
                    if not existing_ev:
                        db_t = plan_task_to_db_task.get(plan_task_id) if plan_task_id else None
                        new_ev = Evidence(
                            id=str(uuid.uuid4()),
                            investigation_id=investigation_id,
                            task_id=db_t.id if db_t else None,
                            source_type=ev_item.get("source_type", "analytical_tool"),
                            source_reference=ev_item.get("source_reference", "consultos_engine"),
                            finding=ev_item.get("finding", "Analytical finding"),
                            supporting_data=ev_item.get("supporting_data"),
                        )
                        evidence_repo.create(new_ev)

                db.commit()

                # Re-verify and re-evaluate
                verified_ev_list = ver_service.verify_investigation_evidence(investigation_id)
                evaluated_hyps = hyp_service.evaluate_investigation_hypotheses(investigation_id)

            # 8. Generate Evidence-Backed Final Report
            report_service = ReportService(db)
            report_service.generate_report(investigation_id)

            # 9. Update final investigation status
            if summary.completed_tasks > 0:
                investigation.status = InvestigationStatus.COMPLETED.value
                status_event_type = "investigation_completed"
            else:
                investigation.status = InvestigationStatus.FAILED.value
                status_event_type = "investigation_failed"

            investigation_event = InvestigationEvent(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                event_type=status_event_type,
                details={
                    "status": investigation.status,
                    "completed_tasks": summary.completed_tasks,
                    "failed_tasks": summary.failed_tasks,
                    "blocked_tasks": summary.blocked_tasks,
                    "replanning_iterations": replan_iter,
                },
            )
            event_repo.create(investigation_event)

            end_event = InvestigationEvent(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                event_type="investigation_execution_finished",
                details={
                    "status": investigation.status,
                    "completed_tasks": summary.completed_tasks,
                    "failed_tasks": summary.failed_tasks,
                    "blocked_tasks": summary.blocked_tasks,
                    "duration_ms": summary.duration_ms,
                    "evidence_count": len(summary.generated_evidence),
                    "replanning_iterations": replan_iter,
                },
            )
            event_repo.create(end_event)

            db.commit()
            db.refresh(investigation)
            logger.info(
                f"Successfully committed Part 3 execution pipeline for investigation '{investigation_id}': "
                f"status={investigation.status}, replans={replan_iter}"
            )
            return summary

        except Exception as exc:
            db.rollback()
            logger.error(
                f"Failed to persist execution outcomes for investigation '{investigation_id}': {exc}",
                exc_info=True,
            )
            raise


engine_adapter = InvestigationEngineAdapter()
