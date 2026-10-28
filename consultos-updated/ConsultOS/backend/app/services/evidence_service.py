from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.evidence import Evidence
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.core.exceptions import InvestigationNotFoundException


class EvidenceService:
    """Service handling evidence queries and operations."""

    def __init__(self, db: Session):
        self.db = db
        self.investigation_repo = InvestigationRepository(db)
        self.evidence_repo = EvidenceRepository(db)

    def list_evidence_for_investigation(
        self,
        investigation_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Evidence], int]:
        """List evidence for an investigation, raising 404 if investigation does not exist."""
        if not self.investigation_repo.exists(investigation_id):
            raise InvestigationNotFoundException(investigation_id)

        return self.evidence_repo.list_by_investigation(
            investigation_id=investigation_id,
            limit=limit,
            offset=offset,
        )
