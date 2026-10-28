import logging
from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.investigation import Investigation, InvestigationStatus
from app.models.event import InvestigationEvent
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.event_repository import EventRepository
from app.core.exceptions import InvestigationNotFoundException, ConsultOSException

logger = logging.getLogger("consultos.services.investigation")


class InvestigationService:
    """Business logic coordinator for business investigations."""

    def __init__(self, db: Session):
        self.db = db
        self.investigation_repo = InvestigationRepository(db)
        self.event_repo = EventRepository(db)

    def create_investigation(self, business_question: str) -> Investigation:
        """Create a new business inquiry and record its creation event atomically."""
        trimmed_question = business_question.strip()
        if not trimmed_question:
            raise ConsultOSException(
                message="Business question cannot be empty or whitespace.",
                code="INVALID_BUSINESS_QUESTION",
                status_code=422,
            )

        try:
            import uuid

            investigation_id = str(uuid.uuid4())
            investigation = Investigation(
                id=investigation_id,
                business_question=trimmed_question,
                status=InvestigationStatus.DRAFT.value,
                current_plan_version=0,
            )
            self.investigation_repo.create(investigation)

            # Record creation event atomically in the same transaction
            creation_event = InvestigationEvent(
                id=str(uuid.uuid4()),
                investigation_id=investigation_id,
                event_type="investigation_created",
                details={"business_question": trimmed_question},
            )
            self.event_repo.create(creation_event)

            self.db.commit()
            self.db.refresh(investigation)
            logger.info(f"Investigation {investigation.id} created successfully.")
            return investigation
        except Exception as exc:
            self.db.rollback()
            logger.error(f"Failed to create investigation: {exc}")
            raise

    def get_investigation(self, investigation_id: str) -> Investigation:
        """Retrieve an investigation by ID or raise InvestigationNotFoundException."""
        investigation = self.investigation_repo.get_by_id(investigation_id)
        if not investigation:
            raise InvestigationNotFoundException(investigation_id)
        return investigation

    def list_investigations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Investigation], int]:
        """List investigations with pagination."""
        return self.investigation_repo.list(limit=limit, offset=offset)
