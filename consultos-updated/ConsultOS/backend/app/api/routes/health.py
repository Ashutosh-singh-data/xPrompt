import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db, check_db_connection
from app.schemas.common import HealthResponse

logger = logging.getLogger("consultos.api.health")
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health Check",
    description="Checks the health of the application and its database connectivity.",
)
def get_health(db: Session = Depends(get_db)):
    """Health endpoint returning actual database connectivity status."""
    is_connected = check_db_connection(db)

    if not is_connected:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "app_name": settings.APP_NAME,
                "database": "disconnected",
            },
        )

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        database="connected",
    )
