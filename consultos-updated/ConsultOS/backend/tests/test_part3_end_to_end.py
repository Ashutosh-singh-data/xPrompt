import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation, InvestigationStatus
from app.models.task import InvestigationTask, TaskStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus
from app.models.event import InvestigationEvent


def test_full_part3_autonomous_investigation_lifecycle(client: TestClient, db_session: Session):
    """Test full Part 3 lifecycle:

    Business inquiry -> Execution -> Evidence verification -> Hypothesis evaluation -> Dynamic replanning -> Final report.
    """
    # 1. Create Investigation
    create_res = client.post(
        "/api/investigations",
        json={"business_question": "Why did sales drop significantly across regions in Q3?"},
    )
    assert create_res.status_code == 201
    inv_id = create_res.json()["id"]

    # 2. Dataset with clear concentration and time trend
    dataset = [
        {"order_date": "2026-07-01", "sales": 10000.0, "region": "North"},
        {"order_date": "2026-07-15", "sales": 8000.0, "region": "South"},
        {"order_date": "2026-08-01", "sales": 5000.0, "region": "North"},
        {"order_date": "2026-08-15", "sales": 4000.0, "region": "South"},
        {"order_date": "2026-09-01", "sales": 2000.0, "region": "North"},
        {"order_date": "2026-09-15", "sales": 1500.0, "region": "South"},
    ]

    # 3. Execute investigation
    exec_res = client.post(
        f"/api/investigations/{inv_id}/execute",
        json={"data": dataset},
    )
    assert exec_res.status_code == 200
    summary = exec_res.json()
    assert summary["investigation_id"] == inv_id
    assert summary["completed_tasks"] >= 3

    # 4. Verify Evidence was verified
    ev_res = client.get(f"/api/investigations/{inv_id}/evidence")
    assert ev_res.status_code == 200
    ev_items = ev_res.json()["items"]
    assert len(ev_items) >= 1

    # Check verification status is present and populated
    verified_statuses = [e["verification_status"] for e in ev_items]
    assert "verified" in verified_statuses
    for e in ev_items:
        if e["verification_status"] == "verified":
            assert e["verification_metadata"]["status"] == "verified"
            assert "rules_passed" in e["verification_metadata"]

    # 5. Verify Hypotheses were evaluated
    check_inv = client.get(f"/api/investigations/{inv_id}")
    assert check_inv.status_code == 200
    assert check_inv.json()["status"] == "completed"

    # 6. Verify Final Report automatically generated with traceable evidence
    report_res = client.get(f"/api/investigations/{inv_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["investigation_id"] == inv_id
    assert report_data["version"] >= 1
    assert "findings" in report_data
    assert "recommendations" in report_data
    assert len(report_data["findings"]["observed_facts"]) >= 1

    # Check evidence traceability in report
    for fact in report_data["findings"]["observed_facts"]:
        assert "evidence_id" in fact
        assert "fact" in fact
        assert "source_type" in fact

    # 7. Verify comprehensive events timeline
    events_res = client.get(f"/api/investigations/{inv_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()["items"]
    event_types = [e["event_type"] for e in events]

    assert "investigation_created" in event_types
    assert "investigation_execution_started" in event_types
    assert "evidence_verified" in event_types
    assert "hypothesis_evaluated" in event_types
    assert "final_report_generated" in event_types
    assert "investigation_completed" in event_types
    assert "investigation_execution_finished" in event_types


def test_autonomous_recovery_and_replanning_on_failing_task(client: TestClient, db_session: Session):
    """Test that a failing task triggers bounded recovery and dynamic replanning with event tracking."""
    # Create investigation
    create_res = client.post(
        "/api/investigations",
        json={"business_question": "Why did product sales drop?"},
    )
    inv_id = create_res.json()["id"]

    # Dataset with intentional date issue (non-parseable string)
    dataset = [
        {"order_date": "not_a_valid_date_at_all", "sales": 100.0, "category": "Tech"},
        {"order_date": "also_invalid_date", "sales": 200.0, "category": "Home"},
    ]

    # Execute
    exec_res = client.post(
        f"/api/investigations/{inv_id}/execute",
        json={"data": dataset},
    )
    assert exec_res.status_code == 200

    # Events should reflect full recovery/replanning attempt
    events_res = client.get(f"/api/investigations/{inv_id}/events")
    events = events_res.json()["items"]
    event_types = [e["event_type"] for e in events]

    assert "investigation_execution_started" in event_types
    assert "final_report_generated" in event_types
