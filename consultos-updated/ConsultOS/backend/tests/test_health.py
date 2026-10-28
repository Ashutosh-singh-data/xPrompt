from unittest.mock import patch
from fastapi.testclient import TestClient
from app.core.config import settings


def test_health_check_success(client: TestClient):
    """Test health endpoint returns expected structure when database is healthy."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.APP_NAME
    assert data["database"] == "connected"


def test_health_check_database_failure(client: TestClient):
    """Test health endpoint returns 503 and unhealthy status when database connectivity fails."""
    with patch("app.api.routes.health.check_db_connection", return_value=False):
        response = client.get("/api/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["app_name"] == settings.APP_NAME
        assert data["database"] == "disconnected"
