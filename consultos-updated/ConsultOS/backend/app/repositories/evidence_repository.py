from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.evidence import Evidence


class EvidenceRepository:
    """Repository handling persistent storage and retrieval of Evidence entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, evidence: Evidence) -> Evidence:
        """Add evidence to the active session."""
        self.db.add(evidence)
        return evidence

    def list_by_investigation(
        self,
        investigation_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Evidence], int]:
        """List evidence belonging strictly to an investigation."""
        count_stmt = (
            select(func.count())
            .select_from(Evidence)
            .where(Evidence.investigation_id == investigation_id)
        )
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            select(Evidence)
            .where(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.execute(stmt).scalars().all())
        return items, total
