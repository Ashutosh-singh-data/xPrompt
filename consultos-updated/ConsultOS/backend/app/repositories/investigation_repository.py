from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.investigation import Investigation


class InvestigationRepository:
    """Repository handling persistent storage and retrieval of Investigation entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, investigation: Investigation) -> Investigation:
        """Add investigation to the active session."""
        self.db.add(investigation)
        return investigation

    def get_by_id(self, investigation_id: str) -> Optional[Investigation]:
        """Retrieve an investigation by its unique identifier."""
        stmt = select(Investigation).where(Investigation.id == investigation_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def exists(self, investigation_id: str) -> bool:
        """Check if an investigation exists without loading full object."""
        stmt = (
            select(func.count(1))
            .select_from(Investigation)
            .where(Investigation.id == investigation_id)
        )
        count = self.db.execute(stmt).scalar() or 0
        return count > 0

    def list(self, limit: int = 20, offset: int = 0) -> Tuple[List[Investigation], int]:
        """List investigations with pagination, ordered newest first."""
        count_stmt = select(func.count()).select_from(Investigation)
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            select(Investigation)
            .order_by(Investigation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.execute(stmt).scalars().all())
        return items, total
