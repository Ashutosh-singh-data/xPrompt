import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.task import InvestigationTask, TaskStatus
from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.services.report_service import ReportService


def test_generate_final_report_structure_and_traceability(db_session: Session):
    """Test generating evidence-backed final report with traceable findings and honest limitations."""
    inv = Investigation(business_question="Why did product churn increase?")
    db_session.add(inv)
    db_session.commit()

    # 1. Add Task
    task = InvestigationTask(
        investigation_id=inv.id,
        title="Analyze category churn",
        task_type="analysis",
        status=TaskStatus.COMPLETED.value,
        result={"groups": [{"category": "Enterprise", "churn_rate": 0.22}]},
    )
    db_session.add(task)
    db_session.commit()

    # 2. Add Verified Evidence
    verified_ev = Evidence(
        investigation_id=inv.id,
        task_id=task.id,
        source_type="aggregation_tool",
        source_reference="tool://grouped_aggregator",
        finding="Primary segment 'Enterprise' leads churn rate at 22%.",
        supporting_data={"top_group": {"category": "Enterprise", "churn_rate": 0.22}},
        verification_status=EvidenceVerificationStatus.VERIFIED.value,
    )

    # 3. Add Inconclusive Evidence
    inconclusive_ev = Evidence(
        investigation_id=inv.id,
        source_type="timeseries_tool",
        source_reference="tool://timeseries_analyzer",
        finding="Time-series trend direction is unknown.",
        supporting_data={"trend_direction": "unknown"},
        verification_status=EvidenceVerificationStatus.INCONCLUSIVE.value,
        verification_metadata={"warnings": ["Trend was unknown"]},
    )

    # 4. Add Hypothesis
    hyp = Hypothesis(
        investigation_id=inv.id,
        statement="The shift in churn is concentrated within specific segments of category rather than uniform.",
        status=HypothesisStatus.SUPPORTED.value,
        confidence=0.85,
    )
    hyp.evidence = [verified_ev]
    db_session.add_all([verified_ev, inconclusive_ev, hyp])
    db_session.commit()

    # Generate report
    report_service = ReportService(db_session)
    report = report_service.generate_report(inv.id)

    assert report.investigation_id == inv.id
    assert report.version == 1
    assert "Why did product churn increase?" in report.executive_summary

    # Verify observed facts reference verified evidence
    findings = report.findings
    assert len(findings["observed_facts"]) == 1
    assert findings["observed_facts"][0]["evidence_id"] == verified_ev.id
    assert findings["observed_facts"][0]["fact"] == verified_ev.finding

    # Verify inconclusive findings are separated
    assert len(findings["inconclusive_or_contradictory_findings"]) == 1
    assert findings["inconclusive_or_contradictory_findings"][0]["evidence_id"] == inconclusive_ev.id

    # Verify recommendations are derived from supported hypothesis
    recommendations = report.recommendations
    assert len(recommendations) >= 1
    assert recommendations[0]["supported_by_hypothesis"] == hyp.id


def test_report_api_endpoints(client: TestClient, db_session: Session):
    """Test GET and POST report endpoints via FastAPI client."""
    inv = Investigation(business_question="API report test")
    db_session.add(inv)
    db_session.commit()

    # Attempt GET before report exists -> 404 with REPORT_NOT_READY
    res_get_before = client.get(f"/api/investigations/{inv.id}/report")
    assert res_get_before.status_code == 404
    assert res_get_before.json()["error"]["code"] == "REPORT_NOT_READY"

    # POST to generate report
    res_post = client.post(f"/api/investigations/{inv.id}/report")
    assert res_post.status_code == 200
    report_data = res_post.json()
    assert report_data["investigation_id"] == inv.id
    assert report_data["version"] == 1
    assert "findings" in report_data

    # GET report now succeeds
    res_get_after = client.get(f"/api/investigations/{inv.id}/report")
    assert res_get_after.status_code == 200
    assert res_get_after.json()["id"] == report_data["id"]
