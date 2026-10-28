from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.task import InvestigationTask
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.task_repository import TaskRepository
from app.core.exceptions import InvestigationNotFoundException


class TaskService:
    """Service handling analytical task queries and operations."""

    def __init__(self, db: Session):
        self.db = db
        self.investigation_repo = InvestigationRepository(db)
        self.task_repo = TaskRepository(db)

    def list_tasks_for_investigation(
        self,
        investigation_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[InvestigationTask], int]:
        """List tasks belonging to an investigation, raising 404 if investigation does not exist."""
        if not self.investigation_repo.exists(investigation_id):
            raise InvestigationNotFoundException(investigation_id)

        return self.task_repo.list_by_investigation(
            investigation_id=investigation_id,
            limit=limit,
            offset=offset,
        )
