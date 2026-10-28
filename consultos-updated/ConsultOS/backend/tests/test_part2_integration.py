from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation


def test_api_plan_preview(client: TestClient):
    """Test previewing an investigation plan without database side effects."""
    payload = {
        "business_question": "Why did sales drop last month?",
        "columns": ["date", "sales", "region"],
    }
    response = client.post("/api/investigations/plan/preview", json=payload)
    assert response.status_code == 200
    plan = response.json()
    assert "plan_id" in plan
    assert len(plan["hypotheses"]) >= 2
    assert len(plan["tasks"]) >= 3


def test_api_plan_validation(client: TestClient):
    """Test plan validation endpoint."""
    # Preview a plan
    preview_res = client.post(
        "/api/investigations/plan/preview",
        json={
            "business_question": "Analyze marketing spend",
            "columns": ["date", "spend", "channel"],
        },
    )
    plan = preview_res.json()

    # Validate valid plan
    val_res = client.post(
        "/api/investigations/plan/validate",
        json={"plan": plan, "available_columns": ["date", "spend", "channel"]},
    )
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True

    # Validate corrupted plan (introduce cycle)
    plan["tasks"][0]["dependency_ids"] = [plan["tasks"][1]["id"]]
    plan["tasks"][1]["dependency_ids"] = [plan["tasks"][0]["id"]]
    invalid_res = client.post(
        "/api/investigations/plan/validate",
        json={"plan": plan, "available_columns": ["date", "spend", "channel"]},
    )
    assert invalid_res.status_code == 200
    assert invalid_res.json()["is_valid"] is False
    assert any("Circular dependency" in err for err in invalid_res.json()["errors"])


def test_api_execute_investigation_end_to_end(client: TestClient, db_session: Session):
    """Test complete end-to-end execution of an investigation plan and database persistence."""
    # 1. Create Investigation
    inv_res = client.post(
        "/api/investigations",
        json={"business_question": "Why did our product sales decline in Q3?"},
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 2. Execution dataset
    test_data = [
        {"order_date": "2026-07-01", "sales": 5000.0, "category": "Electronics"},
        {"order_date": "2026-07-15", "sales": 4500.0, "category": "Apparel"},
        {"order_date": "2026-08-01", "sales": 3200.0, "category": "Electronics"},
        {"order_date": "2026-08-15", "sales": 3100.0, "category": "Apparel"},
        {"order_date": "2026-09-01", "sales": 1800.0, "category": "Electronics"},
        {"order_date": "2026-09-15", "sales": 1700.0, "category": "Apparel"},
    ]

    # 3. Execute plan
    exec_res = client.post(
        f"/api/investigations/{inv_id}/execute",
        json={"data": test_data},
    )
    assert exec_res.status_code == 200
    summary = exec_res.json()
    assert summary["investigation_id"] == inv_id
    assert summary["total_tasks"] >= 3
    assert summary["completed_tasks"] == summary["total_tasks"]
    assert summary["failed_tasks"] == 0

    # 4. Verify Investigation status updated to completed
    check_inv = client.get(f"/api/investigations/{inv_id}")
    assert check_inv.status_code == 200
    assert check_inv.json()["status"] == "completed"
    assert check_inv.json()["current_plan_version"] >= 1

    # 5. Verify tasks persisted and returned by tasks endpoint
    tasks_res = client.get(f"/api/investigations/{inv_id}/tasks")
    assert tasks_res.status_code == 200
    tasks_data = tasks_res.json()
    assert tasks_data["total"] >= 3
    for t in tasks_data["items"]:
        assert t["status"] == "completed"
        assert t["result"] is not None

    # 6. Verify evidence generated and persisted
    ev_res = client.get(f"/api/investigations/{inv_id}/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["total"] >= 1
    findings = [e["finding"] for e in ev_data["items"]]
    assert any("Dataset contains" in f or "trend" in f.lower() or "dimension" in f.lower() for f in findings)

    # 7. Verify execution events logged
    events_res = client.get(f"/api/investigations/{inv_id}/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    event_types = [e["event_type"] for e in events_data["items"]]
    assert "investigation_created" in event_types
    assert "investigation_execution_started" in event_types
    assert "investigation_execution_finished" in event_types
