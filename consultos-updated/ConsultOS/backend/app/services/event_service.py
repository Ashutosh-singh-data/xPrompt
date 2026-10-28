from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.event import InvestigationEvent
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.event_repository import EventRepository
from app.core.exceptions import InvestigationNotFoundException


class EventService:
    """Service handling timeline and audit events for investigations."""

    def __init__(self, db: Session):
        self.db = db
        self.investigation_repo = InvestigationRepository(db)
        self.event_repo = EventRepository(db)

    def list_events_for_investigation(
        self,
        investigation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[InvestigationEvent], int]:
        """List persisted events for an investigation, raising 404 if investigation does not exist."""
        if not self.investigation_repo.exists(investigation_id):
            raise InvestigationNotFoundException(investigation_id)

        return self.event_repo.list_by_investigation(
            investigation_id=investigation_id,
            limit=limit,
            offset=offset,
        )
