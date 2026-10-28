from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.event import InvestigationEvent


class EventRepository:
    """Repository handling persistent storage and retrieval of InvestigationEvent entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, event: InvestigationEvent) -> InvestigationEvent:
        """Add event to the active session."""
        self.db.add(event)
        return event

    def list_by_investigation(
        self,
        investigation_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[InvestigationEvent], int]:
        """List events belonging to an investigation in deterministic chronological order."""
        count_stmt = (
            select(func.count())
            .select_from(InvestigationEvent)
            .where(InvestigationEvent.investigation_id == investigation_id)
        )
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            select(InvestigationEvent)
            .where(InvestigationEvent.investigation_id == investigation_id)
            .order_by(InvestigationEvent.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.execute(stmt).scalars().all())
        return items, total
