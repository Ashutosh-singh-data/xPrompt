from typing import Optional, List, Tuple
from sqlalchemy import select, func, insert
from sqlalchemy.orm import Session, selectinload
from app.models.task import InvestigationTask, task_dependencies
from app.core.exceptions import InvalidRelationshipException


class TaskRepository:
    """Repository handling persistent storage and retrieval of InvestigationTask entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, task: InvestigationTask) -> InvestigationTask:
        """Add a new task to the active session."""
        self.db.add(task)
        return task

    def get_by_id(self, task_id: str) -> Optional[InvestigationTask]:
        """Retrieve a task by ID including its dependencies."""
        stmt = (
            select(InvestigationTask)
            .options(selectinload(InvestigationTask.dependencies))
            .where(InvestigationTask.id == task_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_investigation(
        self,
        investigation_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[InvestigationTask], int]:
        """List tasks belonging to an investigation with pagination."""
        count_stmt = (
            select(func.count())
            .select_from(InvestigationTask)
            .where(InvestigationTask.investigation_id == investigation_id)
        )
        total = self.db.execute(count_stmt).scalar() or 0

        stmt = (
            select(InvestigationTask)
            .options(selectinload(InvestigationTask.dependencies))
            .where(InvestigationTask.investigation_id == investigation_id)
            .order_by(InvestigationTask.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> None:
        """Add a dependency relationship between two tasks."""
        if task_id == depends_on_task_id:
            raise InvalidRelationshipException(
                "A task cannot depend on itself.",
                details={"task_id": task_id, "depends_on_task_id": depends_on_task_id},
            )
        stmt = insert(task_dependencies).values(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )
        self.db.execute(stmt)
