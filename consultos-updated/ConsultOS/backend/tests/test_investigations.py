from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import InvestigationStatus
from app.models.event import InvestigationEvent


def test_create_investigation_success(client: TestClient, db_session: Session):
    """Test valid investigation creation persists investigation and creation event."""
    payload = {"business_question": "What is driving churn in Q3?"}
    response = client.post("/api/investigations", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["business_question"] == "What is driving churn in Q3?"
    assert data["status"] == InvestigationStatus.DRAFT.value
    assert data["current_plan_version"] == 0
    assert "created_at" in data
    assert "updated_at" in data

    # Verify creation event was persisted atomically
    inv_id = data["id"]
    events = (
        db_session.query(InvestigationEvent)
        .filter(InvestigationEvent.investigation_id == inv_id)
        .all()
    )
    assert len(events) == 1
    assert events[0].event_type == "investigation_created"
    assert events[0].details == {"business_question": "What is driving churn in Q3?"}


def test_create_investigation_empty_question(client: TestClient):
    """Test empty business question is rejected with 422 validation error."""
    response = client.post("/api/investigations", json={"business_question": ""})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_investigation_whitespace_only(client: TestClient):
    """Test whitespace-only business question is rejected with 422 validation error."""
    response = client.post("/api/investigations", json={"business_question": "   \n\t   "})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_get_investigation_success(client: TestClient):
    """Test retrieving an existing investigation by id."""
    # Create one first
    create_res = client.post(
        "/api/investigations",
        json={"business_question": "How to optimize cloud spend?"},
    )
    inv_id = create_res.json()["id"]

    response = client.get(f"/api/investigations/{inv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == inv_id
    assert data["business_question"] == "How to optimize cloud spend?"
    assert data["status"] == "draft"


def test_get_investigation_not_found(client: TestClient):
    """Test unknown investigation id returns 404."""
    response = client.get("/api/investigations/non-existent-uuid-123")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_list_investigations_pagination(client: TestClient):
    """Test listing and pagination with limit and offset."""
    # Create 5 distinct investigations
    created_ids = []
    for i in range(5):
        res = client.post(
            "/api/investigations",
            json={"business_question": f"Question {i}: Market analysis"},
        )
        created_ids.append(res.json()["id"])

    # Page 1: limit 2, offset 0
    res_page1 = client.get("/api/investigations?limit=2&offset=0")
    assert res_page1.status_code == 200
    data1 = res_page1.json()
    assert len(data1["items"]) == 2
    assert data1["limit"] == 2
    assert data1["offset"] == 0
    assert data1["total"] >= 5

    # Page 2: limit 2, offset 2
    res_page2 = client.get("/api/investigations?limit=2&offset=2")
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["items"]) == 2
    assert data2["limit"] == 2
    assert data2["offset"] == 2

    # Ensure items on page 1 and page 2 are distinct (deterministic order)
    page1_ids = [item["id"] for item in data1["items"]]
    page2_ids = [item["id"] for item in data2["items"]]
    assert set(page1_ids).isdisjoint(set(page2_ids))
