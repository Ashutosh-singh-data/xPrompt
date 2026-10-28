from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.task import InvestigationTask, TaskStatus
from app.repositories.task_repository import TaskRepository


def test_list_tasks_empty(client: TestClient, db_session: Session):
    """Test empty task list when an investigation has no tasks."""
    inv = Investigation(business_question="Test empty tasks")
    db_session.add(inv)
    db_session.commit()

    response = client.get(f"/api/investigations/{inv.id}/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_tasks_unknown_investigation(client: TestClient):
    """Test 404 response when querying tasks for non-existent investigation."""
    response = client.get("/api/investigations/unknown-id/tasks")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_list_tasks_with_dependencies_and_isolation(client: TestClient, db_session: Session):
    """Test listing tasks including dependency IDs and verifying cross-investigation isolation."""
    task_repo = TaskRepository(db_session)

    # Investigation A
    inv_a = Investigation(business_question="Investigation A")
    # Investigation B
    inv_b = Investigation(business_question="Investigation B")
    db_session.add_all([inv_a, inv_b])
    db_session.commit()

    # Tasks for Inv A
    task_a1 = InvestigationTask(
        investigation_id=inv_a.id,
        title="Extract CRM logs",
        task_type="data_retrieval",
        status=TaskStatus.COMPLETED.value,
    )
    task_a2 = InvestigationTask(
        investigation_id=inv_a.id,
        title="Analyze churn correlation",
        task_type="analysis",
        status=TaskStatus.PENDING.value,
    )
    # Task for Inv B
    task_b1 = InvestigationTask(
        investigation_id=inv_b.id,
        title="Scan market reports",
        task_type="research",
        status=TaskStatus.READY.value,
    )
    db_session.add_all([task_a1, task_a2, task_b1])
    db_session.commit()

    # Add dependency: task_a2 depends on task_a1
    task_repo.add_dependency(task_id=task_a2.id, depends_on_task_id=task_a1.id)
    db_session.commit()

    # Query tasks for Investigation A
    res_a = client.get(f"/api/investigations/{inv_a.id}/tasks")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 2
    task_ids_a = [t["id"] for t in data_a["items"]]
    assert task_a1.id in task_ids_a
    assert task_a2.id in task_ids_a
    assert task_b1.id not in task_ids_a  # Strict isolation!

    # Check dependency IDs
    t2 = next(t for t in data_a["items"] if t["id"] == task_a2.id)
    assert task_a1.id in t2["dependency_ids"]

    # Query tasks for Investigation B
    res_b = client.get(f"/api/investigations/{inv_b.id}/tasks")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["total"] == 1
    assert data_b["items"][0]["id"] == task_b1.id
    assert task_a1.id not in [t["id"] for t in data_b["items"]]
