from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.event_service import EventService
from app.schemas.event import EventListResponse

router = APIRouter(prefix="/investigations", tags=["Events"])


@router.get(
    "/{investigation_id}/events",
    response_model=EventListResponse,
    summary="List Investigation Events",
    description="Retrieve persisted timeline and audit events for an investigation.",
)
def list_events_for_investigation(
    investigation_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Offset index"),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    items, total = service.list_events_for_investigation(
        investigation_id=investigation_id,
        limit=limit,
        offset=offset,
    )
    return EventListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
