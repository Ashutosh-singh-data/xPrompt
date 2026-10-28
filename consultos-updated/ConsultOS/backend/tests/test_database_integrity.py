import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.task import InvestigationTask
from app.models.hypothesis import Hypothesis
from app.models.evidence import Evidence
from app.models.report import FinalReport
from app.repositories.task_repository import TaskRepository
from app.core.exceptions import InvalidRelationshipException


def test_required_fields_enforced(db_session: Session):
    """Test that non-nullable columns without defaults raise IntegrityError on commit."""
    # Investigation requires business_question
    inv = Investigation(business_question=None)
    db_session.add(inv)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_task_attempts_nonnegative_constraint(db_session: Session):
    """Test check constraint: attempts >= 0."""
    inv = Investigation(business_question="Integrity check")
    db_session.add(inv)
    db_session.commit()

    task = InvestigationTask(
        investigation_id=inv.id,
        title="Invalid attempts task",
        attempts=-1,
    )
    db_session.add(task)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_hypothesis_confidence_range_constraint(db_session: Session):
    """Test check constraint: confidence between 0.0 and 1.0."""
    inv = Investigation(business_question="Confidence integrity check")
    db_session.add(inv)
    db_session.commit()

    # Valid confidence
    h_valid = Hypothesis(
        investigation_id=inv.id,
        statement="Valid confidence statement",
        confidence=0.85,
    )
    db_session.add(h_valid)
    db_session.commit()

    # Invalid confidence > 1.0
    h_invalid = Hypothesis(
        investigation_id=inv.id,
        statement="Invalid confidence statement",
        confidence=1.5,
    )
    db_session.add(h_invalid)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_task_self_dependency_rejected(db_session: Session):
    """Test task self-dependency is rejected by repository layer and database check constraint."""
    task_repo = TaskRepository(db_session)
    inv = Investigation(business_question="Self dependency check")
    db_session.add(inv)
    db_session.commit()

    task = InvestigationTask(
        investigation_id=inv.id,
        title="Task cannot depend on itself",
    )
    db_session.add(task)
    db_session.commit()

    # Repository check
    with pytest.raises(InvalidRelationshipException) as exc_info:
        task_repo.add_dependency(task_id=task.id, depends_on_task_id=task.id)
    assert "cannot depend on itself" in str(exc_info.value)


def test_foreign_key_enforcement(db_session: Session):
    """Test foreign key constraint fails when referencing non-existent investigation."""
    task = InvestigationTask(
        investigation_id="non-existent-inv-id",
        title="Orphan task",
    )
    db_session.add(task)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascading_deletion(db_session: Session):
    """Test deleting an investigation cascades and cleans up child entities."""
    inv = Investigation(business_question="Cascade test")
    db_session.add(inv)
    db_session.commit()

    task = InvestigationTask(investigation_id=inv.id, title="Subtask")
    hyp = Hypothesis(investigation_id=inv.id, statement="Sub-hypothesis")
    ev = Evidence(
        investigation_id=inv.id,
        source_type="doc",
        source_reference="ref1",
        finding="Sample finding",
    )
    rep = FinalReport(
        investigation_id=inv.id,
        executive_summary="Summary",
        findings={},
        recommendations={},
        limitations={},
        unresolved_questions={},
    )
    db_session.add_all([task, hyp, ev, rep])
    db_session.commit()

    # Delete investigation
    db_session.delete(inv)
    db_session.commit()

    # Verify children are deleted
    assert db_session.query(InvestigationTask).filter_by(investigation_id=inv.id).first() is None
    assert db_session.query(Hypothesis).filter_by(investigation_id=inv.id).first() is None
    assert db_session.query(Evidence).filter_by(investigation_id=inv.id).first() is None
    assert db_session.query(FinalReport).filter_by(investigation_id=inv.id).first() is None


def test_invalid_cross_investigation_evidence_task_rejected(db_session: Session):
    """Test that associating an evidence record with a task from a different investigation is rejected."""
    inv_1 = Investigation(business_question="Investigation One")
    inv_2 = Investigation(business_question="Investigation Two")
    db_session.add_all([inv_1, inv_2])
    db_session.commit()

    task_of_inv_2 = InvestigationTask(
        investigation_id=inv_2.id,
        title="Task of Investigation Two",
    )
    db_session.add(task_of_inv_2)
    db_session.commit()

    # Attempt to associate Evidence belonging to inv_1 with task_of_inv_2
    invalid_evidence = Evidence(
        investigation_id=inv_1.id,
        task_id=task_of_inv_2.id,  # Mismatch! Belongs to inv_2!
        source_type="log",
        source_reference="system.log",
        finding="Suspicious activity found",
    )
    db_session.add(invalid_evidence)

    with pytest.raises(InvalidRelationshipException) as exc_info:
        db_session.commit()
    assert "Evidence task must belong to the same investigation" in str(exc_info.value)
    db_session.rollback()

