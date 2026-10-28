import pytest
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.task import InvestigationTask, TaskStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.event import InvestigationEvent
from app.services.evidence_verification_service import (
    EvidenceVerificationService,
    VerificationOutcome,
)


def test_verification_never_verifies_simply_because_task_completed(db_session: Session):
    """Ensure evidence is not verified simply because a task completed if findings contradict output."""
    inv = Investigation(business_question="Test verification rules")
    db_session.add(inv)
    db_session.commit()

    # Task completed with 100 rows
    task = InvestigationTask(
        investigation_id=inv.id,
        title="Profiling task",
        task_type="profiling",
        status=TaskStatus.COMPLETED.value,
        result={"row_count": 100, "column_count": 5, "duplicate_rows": 0},
    )
    db_session.add(task)
    db_session.commit()

    # Evidence claiming 999 rows (contradicts task result)
    contradictory_ev = Evidence(
        investigation_id=inv.id,
        task_id=task.id,
        source_type="profiling_tool",
        source_reference="tool://dataset_profiler",
        finding="Dataset contains 999 records across 5 columns.",
        supporting_data={"row_count": 999, "column_count": 5, "duplicate_rows": 0},
    )
    db_session.add(contradictory_ev)
    db_session.commit()

    service = EvidenceVerificationService(db_session)
    outcome = service.verify_evidence(contradictory_ev, task=task)

    # Must be REJECTED despite task completing successfully
    assert outcome.status == EvidenceVerificationStatus.REJECTED
    assert any("contradicts" in r for r in outcome.rejection_reasons)


def test_verification_rejects_evidence_with_failed_task(db_session: Session):
    """Ensure evidence linked to a failed task is rejected."""
    inv = Investigation(business_question="Test failed task evidence")
    db_session.add(inv)
    db_session.commit()

    task = InvestigationTask(
        investigation_id=inv.id,
        title="Failed aggregation",
        task_type="analysis",
        status=TaskStatus.FAILED.value,
        error="Execution failed due to invalid column.",
    )
    db_session.add(task)
    db_session.commit()

    ev = Evidence(
        investigation_id=inv.id,
        task_id=task.id,
        source_type="aggregation_tool",
        source_reference="tool://grouped_aggregator",
        finding="Segment A leads volume.",
        supporting_data={"top_group": {"segment": "A"}},
    )
    db_session.add(ev)
    db_session.commit()

    service = EvidenceVerificationService(db_session)
    outcome = service.verify_evidence(ev, task=task)

    assert outcome.status == EvidenceVerificationStatus.REJECTED
    assert any("not 'completed'" in r for r in outcome.rejection_reasons)


def test_verification_inconclusive_on_empty_dataset(db_session: Session):
    """Ensure evidence from an empty dataset (0 rows) is marked inconclusive."""
    inv = Investigation(business_question="Empty dataset verification")
    db_session.add(inv)
    db_session.commit()

    task = InvestigationTask(
        investigation_id=inv.id,
        title="Profiling empty data",
        task_type="profiling",
        status=TaskStatus.COMPLETED.value,
        result={"row_count": 0, "column_count": 3, "duplicate_rows": 0},
    )
    db_session.add(task)
    db_session.commit()

    ev = Evidence(
        investigation_id=inv.id,
        task_id=task.id,
        source_type="profiling_tool",
        source_reference="tool://dataset_profiler",
        finding="Dataset contains 0 records across 3 columns.",
        supporting_data={"row_count": 0, "column_count": 3, "duplicate_rows": 0},
    )
    db_session.add(ev)
    db_session.commit()

    service = EvidenceVerificationService(db_session)
    outcome = service.verify_evidence(ev, task=task)

    assert outcome.status == EvidenceVerificationStatus.INCONCLUSIVE
    assert any("zero records" in w.lower() for w in outcome.warnings)


def test_verification_success_and_event_logging(db_session: Session):
    """Ensure valid evidence is verified and audit events are generated."""
    inv = Investigation(business_question="Successful verification")
    db_session.add(inv)
    db_session.commit()

    task = InvestigationTask(
        investigation_id=inv.id,
        title="Valid validation",
        task_type="validation",
        status=TaskStatus.COMPLETED.value,
        result={"is_valid": True, "issues": [], "total_rows": 50},
    )
    db_session.add(task)
    db_session.commit()

    ev = Evidence(
        investigation_id=inv.id,
        task_id=task.id,
        source_type="validation_tool",
        source_reference="tool://data_validator",
        finding="Data quality check passed with 0 critical issues.",
        supporting_data={"is_valid": True, "issues": []},
    )
    db_session.add(ev)
    db_session.commit()

    service = EvidenceVerificationService(db_session)
    verified_list = service.verify_investigation_evidence(inv.id)

    assert len(verified_list) == 1
    assert verified_list[0].verification_status == EvidenceVerificationStatus.VERIFIED.value
    assert verified_list[0].verification_metadata["status"] == "verified"

    # Check event created
    events = (
        db_session.query(InvestigationEvent)
        .filter(InvestigationEvent.investigation_id == inv.id)
        .all()
    )
    assert any(e.event_type == "evidence_verified" for e in events)


def test_contradictory_evidence_detection(db_session: Session):
    """Ensure contradiction across sibling evidence items is detected and flagged."""
    inv = Investigation(business_question="Contradiction check")
    db_session.add(inv)
    db_session.commit()

    task1 = InvestigationTask(
        investigation_id=inv.id,
        title="Validation 1",
        task_type="validation",
        status=TaskStatus.COMPLETED.value,
        result={"is_valid": True, "issues": []},
    )
    task2 = InvestigationTask(
        investigation_id=inv.id,
        title="Validation 2",
        task_type="validation",
        status=TaskStatus.COMPLETED.value,
        result={"is_valid": False, "issues": [{"type": "negative_values", "severity": "high"}]},
    )
    db_session.add_all([task1, task2])
    db_session.commit()

    ev1 = Evidence(
        investigation_id=inv.id,
        task_id=task1.id,
        source_type="validation_tool",
        source_reference="tool://data_validator",
        finding="Data quality check passed.",
        supporting_data={"is_valid": True, "issues": []},
    )
    ev2 = Evidence(
        investigation_id=inv.id,
        task_id=task2.id,
        source_type="validation_tool",
        source_reference="tool://data_validator",
        finding="Data quality check failed with critical issues.",
        supporting_data={"is_valid": False, "issues": [{"type": "negative_values", "severity": "high"}]},
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    service = EvidenceVerificationService(db_session)
    outcome = service.verify_evidence(ev1, task=task1, sibling_evidence=[ev1, ev2])

    assert any("Contradictory" in w for w in outcome.warnings)
