from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.report import FinalReport


def test_get_report_unknown_investigation(client: TestClient):
    """Test 404 response with INVESTIGATION_NOT_FOUND when investigation does not exist."""
    response = client.get("/api/investigations/unknown-inv-id/report")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_get_report_not_ready_when_absent(client: TestClient, db_session: Session):
    """Test clear not-ready response when investigation exists but report has not been generated."""
    inv = Investigation(business_question="What is our expansion plan?")
    db_session.add(inv)
    db_session.commit()

    response = client.get(f"/api/investigations/{inv.id}/report")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "REPORT_NOT_READY"
    assert "Report is not ready" in data["error"]["message"]


def test_get_report_success_when_present(client: TestClient, db_session: Session):
    """Test retrieving finalized report when one is present."""
    inv = Investigation(business_question="Why did Q2 revenue miss target?")
    db_session.add(inv)
    db_session.commit()

    report = FinalReport(
        investigation_id=inv.id,
        version=1,
        executive_summary="Revenue missed target due to enterprise pipeline delays.",
        findings={"delays": ["Product launch delayed by 4 weeks", "Sales cycle elongated"]},
        recommendations={"action": "Accelerate QA pipeline and implement pricing incentive"},
        limitations={"sample_size": "Limited to North America accounts"},
        unresolved_questions={"long_term": "Impact on customer lifetime value"},
    )
    db_session.add(report)
    db_session.commit()

    response = client.get(f"/api/investigations/{inv.id}/report")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report.id
    assert data["investigation_id"] == inv.id
    assert data["version"] == 1
    assert data["executive_summary"] == "Revenue missed target due to enterprise pipeline delays."
    assert "delays" in data["findings"]
    assert "action" in data["recommendations"]
