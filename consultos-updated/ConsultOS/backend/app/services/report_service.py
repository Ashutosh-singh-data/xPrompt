import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.report import FinalReport
from app.models.investigation import Investigation
from app.models.task import InvestigationTask, TaskStatus
from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.event import InvestigationEvent
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.event_repository import EventRepository
from app.core.exceptions import (
    InvestigationNotFoundException,
    ReportNotReadyException,
)

logger = logging.getLogger("consultos.services.report_service")


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReportService:
    """Service handling finalized synthesis reports backed by verified empirical evidence."""

    def __init__(self, db: Session):
        self.db = db
        self.investigation_repo = InvestigationRepository(db)
        self.report_repo = ReportRepository(db)
        self.event_repo = EventRepository(db)

    def get_report_for_investigation(self, investigation_id: str) -> FinalReport:
        """Retrieve the latest report for an investigation."""
        if not self.investigation_repo.exists(investigation_id):
            raise InvestigationNotFoundException(investigation_id)

        report = self.report_repo.get_latest_by_investigation(investigation_id)
        if not report:
            raise ReportNotReadyException(investigation_id)

        return report

    def generate_report(self, investigation_id: str) -> FinalReport:
        """Generate and persist an evidence-backed final report for an investigation."""
        investigation = self.investigation_repo.get_by_id(investigation_id)
        if not investigation:
            raise InvestigationNotFoundException(investigation_id)

        tasks = (
            self.db.query(InvestigationTask)
            .filter(InvestigationTask.investigation_id == investigation_id)
            .order_by(InvestigationTask.created_at.asc())
            .all()
        )

        hypotheses = (
            self.db.query(Hypothesis)
            .filter(Hypothesis.investigation_id == investigation_id)
            .order_by(Hypothesis.created_at.asc())
            .all()
        )

        evidence_list = (
            self.db.query(Evidence)
            .filter(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.created_at.asc())
            .all()
        )

        verified_evidence = [
            e for e in evidence_list if e.verification_status == EvidenceVerificationStatus.VERIFIED.value
        ]
        rejected_evidence = [
            e for e in evidence_list if e.verification_status == EvidenceVerificationStatus.REJECTED.value
        ]
        inconclusive_evidence = [
            e for e in evidence_list if e.verification_status in [
                EvidenceVerificationStatus.INCONCLUSIVE.value,
                EvidenceVerificationStatus.UNVERIFIED.value,
            ]
        ]

        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED.value]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED.value]
        blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED.value]

        # 1. Structure Findings
        observed_facts = [
            {
                "evidence_id": e.id,
                "fact": e.finding,
                "source_type": e.source_type,
                "source_reference": e.source_reference,
                "task_id": e.task_id,
                "supporting_data": e.supporting_data,
            }
            for e in verified_evidence
        ]

        hyp_evals = [
            {
                "hypothesis_id": h.id,
                "statement": h.statement,
                "status": h.status,
                "confidence": h.confidence,
                "evidence_ids": [ev.id for ev in h.evidence],
            }
            for h in hypotheses
        ]

        inconclusive_or_contradictory = [
            {
                "evidence_id": e.id,
                "finding": e.finding,
                "verification_status": e.verification_status,
                "reasons": (
                    (e.verification_metadata or {}).get("rejection_reasons", [])
                    + (e.verification_metadata or {}).get("warnings", [])
                ),
            }
            for e in (rejected_evidence + inconclusive_evidence)
        ]

        findings_payload = {
            "business_question": investigation.business_question,
            "observed_facts": observed_facts,
            "hypotheses_evaluations": hyp_evals,
            "inconclusive_or_contradictory_findings": inconclusive_or_contradictory,
            "verified_evidence_count": len(verified_evidence),
            "total_evidence_count": len(evidence_list),
        }

        # 2. Structure Limitations
        data_quality_issues = []
        for e in verified_evidence:
            if e.source_type == "validation_tool":
                sup = e.supporting_data or {}
                issues = sup.get("issues", [])
                if issues:
                    data_quality_issues.extend(issues)

        limitations_payload = {
            "data_quality_constraints": data_quality_issues,
            "unverified_evidence_count": len(rejected_evidence) + len(inconclusive_evidence),
            "failed_tasks_count": len(failed_tasks),
            "blocked_tasks_count": len(blocked_tasks),
            "data_completeness_notes": (
                "Data quality issues detected that may skew interpretations."
                if data_quality_issues
                else "Baseline data quality constraints satisfied."
            ),
        }

        # 3. Structure Unresolved Questions
        failed_task_impacts = [
            {
                "task_id": t.id,
                "title": t.title,
                "status": t.status,
                "impact": f"Task execution failed: {t.error}",
            }
            for t in (failed_tasks + blocked_tasks)
        ]

        inconclusive_hyp_notes = [
            {
                "hypothesis_id": h.id,
                "statement": h.statement,
                "uncertainty": "Data was insufficient or inconclusive to confirm or refute assertion.",
            }
            for h in hypotheses
            if h.status == HypothesisStatus.INCONCLUSIVE.value
        ]

        unresolved_questions_payload = {
            "failed_or_blocked_tasks": failed_task_impacts,
            "inconclusive_hypotheses": inconclusive_hyp_notes,
            "has_unresolved_questions": bool(failed_task_impacts or inconclusive_hyp_notes),
        }

        # 4. Structure Recommendations
        recommendations_payload: List[Dict[str, Any]] = []

        # Generate evidence-supported recommendations
        for h in hypotheses:
            if h.status == HypothesisStatus.SUPPORTED.value:
                if "segment" in h.statement.lower() or "concentrated" in h.statement.lower():
                    # Pick top segment fact
                    top_fact = next((f["fact"] for f in observed_facts if "segment" in f["fact"].lower() or "leads" in f["fact"].lower()), None)
                    recommendations_payload.append({
                        "category": "Strategic Focus",
                        "recommendation": (
                            f"Prioritize operational initiatives around top-performing segment identified in verified findings: {top_fact}"
                            if top_fact
                            else "Focus operational resources on primary contributing segments."
                        ),
                        "supported_by_hypothesis": h.id,
                        "type": "empirical_recommendation",
                    })
                elif "temporal" in h.statement.lower() or "time" in h.statement.lower():
                    top_ts = next((f["fact"] for f in observed_facts if "trend" in f["fact"].lower()), None)
                    recommendations_payload.append({
                        "category": "Timing & Interventions",
                        "recommendation": (
                            f"Align operational adjustments with verified temporal cycles: {top_ts}"
                            if top_ts
                            else "Plan interventions considering identified time intervals."
                        ),
                        "supported_by_hypothesis": h.id,
                        "type": "empirical_recommendation",
                    })
                elif "data quality" in h.statement.lower():
                    recommendations_payload.append({
                        "category": "Data Governance",
                        "recommendation": "Remediate upstream data pipeline integrity issues identified during data validation.",
                        "supported_by_hypothesis": h.id,
                        "type": "empirical_recommendation",
                    })

        if not recommendations_payload:
            recommendations_payload.append({
                "category": "Telemetry & Data Collection",
                "recommendation": (
                    "Available evidence is inconclusive to support definitive business actions. "
                    "Recommend expanding data capture and instrumentation before proceeding."
                ),
                "supported_by_hypothesis": None,
                "type": "precautionary_recommendation",
            })

        # 5. Executive Summary
        exec_lines = [
            f"Investigation regarding '{investigation.business_question}' concluded.",
            f"Executed {len(completed_tasks)} analytical tasks with {len(verified_evidence)} verified empirical findings.",
        ]

        supported_hyps = [h for h in hypotheses if h.status == HypothesisStatus.SUPPORTED.value]
        if supported_hyps:
            exec_lines.append(f"Supported hypotheses: {', '.join(h.statement for h in supported_hyps)}.")

        contradicted_hyps = [h for h in hypotheses if h.status == HypothesisStatus.CONTRADICTED.value]
        if contradicted_hyps:
            exec_lines.append(f"Contradicted hypotheses: {', '.join(h.statement for h in contradicted_hyps)}.")

        inconclusive_hyps = [h for h in hypotheses if h.status == HypothesisStatus.INCONCLUSIVE.value]
        if inconclusive_hyps:
            exec_lines.append(f"Remaining uncertainties: {len(inconclusive_hyps)} hypotheses remain inconclusive due to data limitations.")

        executive_summary = " ".join(exec_lines)

        # 6. Versioning and Persistence
        latest_report = self.report_repo.get_latest_by_investigation(investigation_id)
        version = (latest_report.version + 1) if latest_report else 1

        final_report = FinalReport(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            version=version,
            executive_summary=executive_summary,
            findings=findings_payload,
            recommendations=recommendations_payload,
            limitations=limitations_payload,
            unresolved_questions=unresolved_questions_payload,
            created_at=get_utc_now(),
        )

        self.report_repo.create(final_report)

        # Record audit event
        event = InvestigationEvent(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            event_type="final_report_generated",
            details={
                "report_id": final_report.id,
                "version": version,
                "verified_facts_count": len(observed_facts),
                "supported_hypotheses_count": len(supported_hyps),
                "unresolved_questions_count": len(inconclusive_hyps),
            },
        )
        self.event_repo.create(event)

        self.db.commit()
        self.db.refresh(final_report)
        logger.info(
            f"Generated final report v{version} for investigation '{investigation_id}'."
        )
        return final_report
