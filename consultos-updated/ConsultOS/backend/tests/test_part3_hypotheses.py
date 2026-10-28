import pytest
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.event import InvestigationEvent
from app.services.hypothesis_evaluation_service import HypothesisEvaluationService


def test_hypothesis_supported_by_verified_evidence(db_session: Session):
    """Ensure hypothesis is marked supported when verified evidence supports assertion."""
    inv = Investigation(business_question="Why did product churn increase?")
    db_session.add(inv)
    db_session.commit()

    hyp = Hypothesis(
        investigation_id=inv.id,
        statement="The shift in sales is concentrated within specific segments of category rather than uniform.",
        status=HypothesisStatus.PROPOSED.value,
    )
    db_session.add(hyp)

    # Verified evidence showing top group dominance
    ev = Evidence(
        investigation_id=inv.id,
        source_type="aggregation_tool",
        source_reference="tool://grouped_aggregator",
        finding="Primary segment 'Electronics' for dimension 'category' leads metric volume.",
        supporting_data={"top_group": {"category": "Electronics", "sales_sum": 50000}, "total_groups": 4},
        verification_status=EvidenceVerificationStatus.VERIFIED.value,
    )
    db_session.add(ev)
    db_session.commit()

    service = HypothesisEvaluationService(db_session)
    evaluated = service.evaluate_investigation_hypotheses(inv.id)

    assert len(evaluated) == 1
    assert evaluated[0].status == HypothesisStatus.SUPPORTED.value
    assert evaluated[0].confidence is not None
    assert evaluated[0].confidence >= 0.75
    # Verify evidence relationship preserved
    assert len(evaluated[0].evidence) == 1
    assert evaluated[0].evidence[0].id == ev.id


def test_hypothesis_contradicted_by_verified_clean_data(db_session: Session):
    """Ensure data quality hypothesis is contradicted when verified data is clean."""
    inv = Investigation(business_question="Are anomalies due to data quality?")
    db_session.add(inv)
    db_session.commit()

    hyp = Hypothesis(
        investigation_id=inv.id,
        statement="Data quality issues, such as missing entries or duplicate records, account for metric anomalies.",
        status=HypothesisStatus.PROPOSED.value,
    )
    db_session.add(hyp)

    # Verified validation showing 0 issues and is_valid True
    ev = Evidence(
        investigation_id=inv.id,
        source_type="validation_tool",
        source_reference="tool://data_validator",
        finding="Data quality check passed with 0 critical issues.",
        supporting_data={"is_valid": True, "issues": []},
        verification_status=EvidenceVerificationStatus.VERIFIED.value,
    )
    db_session.add(ev)
    db_session.commit()

    service = HypothesisEvaluationService(db_session)
    evaluated = service.evaluate_investigation_hypotheses(inv.id)

    assert len(evaluated) == 1
    # Contradicted because data is clean!
    assert evaluated[0].status == HypothesisStatus.CONTRADICTED.value
    assert evaluated[0].confidence >= 0.80


def test_hypothesis_inconclusive_when_evidence_is_insufficient_or_rejected(db_session: Session):
    """Ensure hypothesis remains inconclusive when evidence was rejected or insufficient."""
    inv = Investigation(business_question="Temporal analysis")
    db_session.add(inv)
    db_session.commit()

    hyp = Hypothesis(
        investigation_id=inv.id,
        statement="The variance in revenue is concentrated in specific time intervals across order_date.",
        status=HypothesisStatus.PROPOSED.value,
    )
    db_session.add(hyp)

    # Rejected evidence cannot support hypothesis
    rejected_ev = Evidence(
        investigation_id=inv.id,
        source_type="timeseries_tool",
        source_reference="tool://timeseries_analyzer",
        finding="Time-series trend observed is 'increasing'.",
        supporting_data={"trend_direction": "increasing", "overall_change_pct": 25.0},
        verification_status=EvidenceVerificationStatus.REJECTED.value,
    )
    db_session.add(rejected_ev)
    db_session.commit()

    service = HypothesisEvaluationService(db_session)
    evaluated = service.evaluate_investigation_hypotheses(inv.id)

    assert len(evaluated) == 1
    assert evaluated[0].status == HypothesisStatus.INCONCLUSIVE.value
    assert evaluated[0].confidence is None
    # No verified evidence linked
    assert len(evaluated[0].evidence) == 0


def test_hypothesis_evaluation_records_events(db_session: Session):
    """Ensure hypothesis evaluation records audit events."""
    inv = Investigation(business_question="Audit event verification")
    db_session.add(inv)
    db_session.commit()

    hyp = Hypothesis(
        investigation_id=inv.id,
        statement="Data quality issues, such as missing entries or duplicate records, account for metric anomalies.",
        status=HypothesisStatus.PROPOSED.value,
    )
    db_session.add(hyp)
    db_session.commit()

    service = HypothesisEvaluationService(db_session)
    service.evaluate_investigation_hypotheses(inv.id)

    events = (
        db_session.query(InvestigationEvent)
        .filter(
            InvestigationEvent.investigation_id == inv.id,
            InvestigationEvent.event_type == "hypothesis_evaluated",
        )
        .all()
    )
    assert len(events) == 1
    assert events[0].details["hypothesis_id"] == hyp.id
