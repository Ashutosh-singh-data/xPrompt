from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.evidence import Evidence


def test_list_evidence_unknown_investigation(client: TestClient):
    """Test 404 response when querying evidence for unknown investigation."""
    response = client.get("/api/investigations/unknown-id/evidence")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_list_evidence_empty(client: TestClient, db_session: Session):
    """Test empty evidence list when none has been recorded."""
    inv = Investigation(business_question="Evidence test inquiry")
    db_session.add(inv)
    db_session.commit()

    response = client.get(f"/api/investigations/{inv.id}/evidence")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_evidence_and_isolation(client: TestClient, db_session: Session):
    """Test evidence listing and ensure evidence from other investigations is never leaked."""
    inv_1 = Investigation(business_question="Inquiry 1")
    inv_2 = Investigation(business_question="Inquiry 2")
    db_session.add_all([inv_1, inv_2])
    db_session.commit()

    ev1 = Evidence(
        investigation_id=inv_1.id,
        source_type="file",
        source_reference="s3://metrics/churn.csv",
        finding="Customer churn increased by 14% in Enterprise tier.",
        supporting_data={"pct_increase": 14, "tier": "enterprise"},
    )
    ev2 = Evidence(
        investigation_id=inv_2.id,
        source_type="interview",
        source_reference="Transcript: VP Sales",
        finding="Discount approvals were delayed by 8 days.",
        supporting_data={"delay_days": 8},
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    # Query for inv_1
    res1 = client.get(f"/api/investigations/{inv_1.id}/evidence")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 1
    assert data1["items"][0]["id"] == ev1.id
    assert data1["items"][0]["finding"] == "Customer churn increased by 14% in Enterprise tier."
    assert data1["items"][0]["supporting_data"] == {"pct_increase": 14, "tier": "enterprise"}

    # Query for inv_2
    res2 = client.get(f"/api/investigations/{inv_2.id}/evidence")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["id"] == ev2.id
    assert data2["items"][0]["finding"] == "Discount approvals were delayed by 8 days."
