import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.task import InvestigationTask, TaskStatus
from app.models.event import InvestigationEvent
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.event_repository import EventRepository

logger = logging.getLogger("consultos.services.evidence_verification")


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationOutcome:
    """Encapsulates the result of verifying a single evidence record."""

    def __init__(
        self,
        status: EvidenceVerificationStatus,
        rules_passed: List[str],
        rejection_reasons: List[str],
        warnings: List[str],
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status = status
        self.rules_passed = rules_passed
        self.rejection_reasons = rejection_reasons
        self.warnings = warnings
        self.details = details or {}

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "verified_at": get_utc_now().isoformat(),
            "status": self.status.value,
            "rules_passed": self.rules_passed,
            "rejection_reasons": self.rejection_reasons,
            "warnings": self.warnings,
            "details": self.details,
        }


class EvidenceVerificationService:
    """Rule-based verification service that validates evidence artifacts against analytical tool executions.

    Enforces that evidence is never verified simply because a task completed successfully.
    Performs structural, consistency, output fidelity, and contradiction checks.
    """

    def __init__(self, db: Session):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.task_repo = TaskRepository(db)
        self.event_repo = EventRepository(db)

    def verify_evidence(
        self,
        evidence: Evidence,
        task: Optional[InvestigationTask] = None,
        sibling_evidence: Optional[List[Evidence]] = None,
    ) -> VerificationOutcome:
        """Verify a single Evidence record according to deterministic validation rules."""
        rules_passed: List[str] = []
        rejection_reasons: List[str] = []
        warnings: List[str] = []

        # Rule 1: Task linkage and execution success
        # An evidence item claiming analytical origin MUST have an associated task that completed successfully
        if not evidence.task_id:
            # Unlinked evidence cannot be verified against analytical tool execution
            return VerificationOutcome(
                status=EvidenceVerificationStatus.INCONCLUSIVE,
                rules_passed=[],
                rejection_reasons=[],
                warnings=["Evidence has no associated task_id to verify analytical outputs against."],
            )

        resolved_task = task
        if resolved_task is None:
            resolved_task = self.task_repo.get_by_id(evidence.task_id)

        if resolved_task is None:
            return VerificationOutcome(
                status=EvidenceVerificationStatus.REJECTED,
                rules_passed=[],
                rejection_reasons=[f"Associated task '{evidence.task_id}' was not found."],
                warnings=[],
            )

        if resolved_task.status != TaskStatus.COMPLETED.value:
            return VerificationOutcome(
                status=EvidenceVerificationStatus.REJECTED,
                rules_passed=[],
                rejection_reasons=[
                    f"Associated task '{resolved_task.id}' status is '{resolved_task.status}', not 'completed'."
                ],
                warnings=[],
            )

        if resolved_task.result is None:
            return VerificationOutcome(
                status=EvidenceVerificationStatus.REJECTED,
                rules_passed=["task_status_completed"],
                rejection_reasons=["Associated task completed but has null or empty execution result."],
                warnings=[],
            )

        rules_passed.append("task_execution_succeeded")

        # Rule 2: Supporting data structure and completeness
        supporting = evidence.supporting_data
        if not supporting or not isinstance(supporting, dict):
            return VerificationOutcome(
                status=EvidenceVerificationStatus.INCONCLUSIVE,
                rules_passed=rules_passed,
                rejection_reasons=[],
                warnings=["Evidence is missing structured supporting_data dictionary."],
            )

        rules_passed.append("supporting_data_structured")

        # Rule 3: Tool-specific structure & consistency validation
        tool_name = evidence.source_reference.replace("tool://", "")
        task_res = resolved_task.result if isinstance(resolved_task.result, dict) else {}

        if "profiler" in tool_name or evidence.source_type == "profiling_tool":
            row_count = supporting.get("row_count")
            col_count = supporting.get("column_count")
            dup_rows = supporting.get("duplicate_rows", 0)

            if row_count is None or col_count is None:
                rejection_reasons.append("Profiling evidence missing 'row_count' or 'column_count'.")
            elif row_count < 0 or col_count < 0:
                rejection_reasons.append("Profiling counts cannot be negative.")
            elif dup_rows > row_count:
                rejection_reasons.append(f"Duplicate rows ({dup_rows}) exceeds total rows ({row_count}).")
            elif row_count == 0:
                # 0 rows is valid execution but inconclusive evidence
                warnings.append("Dataset has zero records; profiling results are inconclusive.")
                return VerificationOutcome(
                    status=EvidenceVerificationStatus.INCONCLUSIVE,
                    rules_passed=rules_passed,
                    rejection_reasons=[],
                    warnings=warnings,
                )
            else:
                # Check fidelity against task output
                actual_rows = task_res.get("row_count")
                if actual_rows is not None and actual_rows != row_count:
                    rejection_reasons.append(
                        f"Evidence row_count ({row_count}) contradicts task result ({actual_rows})."
                    )
                else:
                    rules_passed.append("profiling_metrics_consistent")

        elif "validator" in tool_name or evidence.source_type == "validation_tool":
            is_valid = supporting.get("is_valid")
            issues = supporting.get("issues")

            if is_valid is None:
                rejection_reasons.append("Validation evidence missing 'is_valid' boolean flag.")
            elif not isinstance(issues, list):
                warnings.append("Validation evidence 'issues' is not a list.")
            else:
                actual_valid = task_res.get("is_valid")
                if actual_valid is not None and actual_valid != is_valid:
                    rejection_reasons.append(
                        f"Evidence is_valid ({is_valid}) contradicts task result is_valid ({actual_valid})."
                    )
                else:
                    rules_passed.append("validation_metrics_consistent")

        elif "aggregator" in tool_name or evidence.source_type == "aggregation_tool":
            top_group = supporting.get("top_group")
            total_groups = supporting.get("total_groups", 0)

            if total_groups == 0 or not top_group:
                warnings.append("Aggregator evidence returned zero groups; results are inconclusive.")
                return VerificationOutcome(
                    status=EvidenceVerificationStatus.INCONCLUSIVE,
                    rules_passed=rules_passed,
                    rejection_reasons=[],
                    warnings=warnings,
                )

            # Check that top_group actually exists in task groups
            task_groups = task_res.get("groups", [])
            if task_groups and isinstance(task_groups, list):
                if not any(isinstance(g, dict) and all(top_group.get(k) == g.get(k) for k in top_group) for g in task_groups):
                    rejection_reasons.append("Evidence top_group not found in task execution groups.")
                else:
                    rules_passed.append("aggregation_results_verified")
            else:
                rules_passed.append("aggregation_structure_valid")

        elif "timeseries" in tool_name or evidence.source_type == "timeseries_tool":
            trend = supporting.get("trend_direction")
            if not trend or trend == "unknown":
                warnings.append("Timeseries trend direction is unknown or undetermined.")
                return VerificationOutcome(
                    status=EvidenceVerificationStatus.INCONCLUSIVE,
                    rules_passed=rules_passed,
                    rejection_reasons=[],
                    warnings=warnings,
                )

            actual_trend = task_res.get("trend_direction")
            if actual_trend and actual_trend != trend:
                rejection_reasons.append(
                    f"Evidence trend '{trend}' contradicts task output trend '{actual_trend}'."
                )
            else:
                rules_passed.append("timeseries_trend_verified")

        # Rule 4: Contradiction Detection across sibling evidence
        if sibling_evidence:
            for sibling in sibling_evidence:
                if sibling.id == evidence.id:
                    continue
                # Check for contradictory validation claims
                if evidence.source_type == "validation_tool" and sibling.source_type == "validation_tool":
                    sib_sup = sibling.supporting_data or {}
                    if (supporting.get("is_valid") is True and sib_sup.get("is_valid") is False):
                        warnings.append(
                            f"Contradictory data validation outcome observed with evidence '{sibling.id}'."
                        )
                # Check for contradictory timeseries trend claims
                elif evidence.source_type == "timeseries_tool" and sibling.source_type == "timeseries_tool":
                    sib_sup = sibling.supporting_data or {}
                    t1 = supporting.get("trend_direction")
                    t2 = sib_sup.get("trend_direction")
                    if t1 and t2 and ((t1 == "increasing" and t2 == "decreasing") or (t1 == "decreasing" and t2 == "increasing")):
                        warnings.append(
                            f"Contradictory trend directions ('{t1}' vs '{t2}') observed with evidence '{sibling.id}'."
                        )

        # Final determination
        if rejection_reasons:
            status = EvidenceVerificationStatus.REJECTED
        elif warnings and ("inconclusive" in " ".join(warnings).lower()):
            status = EvidenceVerificationStatus.INCONCLUSIVE
        else:
            status = EvidenceVerificationStatus.VERIFIED

        return VerificationOutcome(
            status=status,
            rules_passed=rules_passed,
            rejection_reasons=rejection_reasons,
            warnings=warnings,
            details={"task_id": resolved_task.id, "tool_name": tool_name},
        )

    def verify_investigation_evidence(
        self,
        investigation_id: str,
    ) -> List[Evidence]:
        """Verify all evidence records associated with an investigation and persist verification states."""
        evidence_list, _ = self.evidence_repo.list_by_investigation(
            investigation_id=investigation_id,
            limit=500,
            offset=0,
        )

        if not evidence_list:
            logger.info(f"No evidence to verify for investigation '{investigation_id}'.")
            return []

        # Pre-fetch tasks for efficiency
        tasks, _ = self.task_repo.list_by_investigation(
            investigation_id=investigation_id,
            limit=500,
            offset=0,
        )
        task_map = {t.id: t for t in tasks}

        for ev in evidence_list:
            task = task_map.get(ev.task_id) if ev.task_id else None
            outcome = self.verify_evidence(
                evidence=ev,
                task=task,
                sibling_evidence=evidence_list,
            )

            previous_status = ev.verification_status
            ev.verification_status = outcome.status.value
            ev.verification_metadata = outcome.to_metadata()

            # Record audit event
            event_type = f"evidence_{outcome.status.value}"
            event = InvestigationEvent(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                task_id=ev.task_id,
                event_type=event_type,
                details={
                    "evidence_id": ev.id,
                    "previous_status": previous_status,
                    "new_status": ev.verification_status,
                    "rules_passed": outcome.rules_passed,
                    "rejection_reasons": outcome.rejection_reasons,
                    "warnings": outcome.warnings,
                },
            )
            self.event_repo.create(event)

        self.db.commit()
        logger.info(
            f"Verified {len(evidence_list)} evidence items for investigation '{investigation_id}'."
        )
        return evidence_list
