from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.events import router as events_router
from app.api.routes.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(investigations_router)
api_router.include_router(tasks_router)
api_router.include_router(evidence_router)
api_router.include_router(events_router)
api_router.include_router(reports_router)
