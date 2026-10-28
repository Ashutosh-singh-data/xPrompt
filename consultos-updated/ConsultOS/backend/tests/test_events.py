from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.event import InvestigationEvent


def test_list_events_unknown_investigation(client: TestClient):
    """Test 404 response when querying events for non-existent investigation."""
    response = client.get("/api/investigations/unknown-id/events")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_event_persistence_and_retrieval(client: TestClient, db_session: Session):
    """Test event persistence on creation and subsequent event queries."""
    # Create investigation via API
    res = client.post(
        "/api/investigations",
        json={"business_question": "Why did server costs spike in June?"},
    )
    assert res.status_code == 201
    inv_id = res.json()["id"]

    # Query events
    events_res = client.get(f"/api/investigations/{inv_id}/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    assert events_data["total"] >= 1
    assert events_data["items"][0]["event_type"] == "investigation_created"
    assert events_data["items"][0]["investigation_id"] == inv_id


def test_event_isolation(client: TestClient, db_session: Session):
    """Test events are strictly isolated between investigations."""
    inv_a = Investigation(business_question="Question A")
    inv_b = Investigation(business_question="Question B")
    db_session.add_all([inv_a, inv_b])
    db_session.commit()

    ev_a = InvestigationEvent(
        investigation_id=inv_a.id,
        event_type="test_event_a",
        details={"status": "ok"},
    )
    ev_b = InvestigationEvent(
        investigation_id=inv_b.id,
        event_type="test_event_b",
        details={"status": "warning"},
    )
    db_session.add_all([ev_a, ev_b])
    db_session.commit()

    res_a = client.get(f"/api/investigations/{inv_a.id}/events")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 1
    assert data_a["items"][0]["id"] == ev_a.id
    assert data_a["items"][0]["event_type"] == "test_event_a"

    res_b = client.get(f"/api/investigations/{inv_b.id}/events")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total"] == 1
    assert data_b["items"][0]["id"] == ev_b.id
    assert data_b["items"][0]["event_type"] == "test_event_b"
