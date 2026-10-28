from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.task_service import TaskService
from app.schemas.task import TaskListResponse

router = APIRouter(prefix="/investigations", tags=["Tasks"])


@router.get(
    "/{investigation_id}/tasks",
    response_model=TaskListResponse,
    summary="List Investigation Tasks",
    description="Retrieve tasks belonging to the specified investigation with dependency IDs.",
)
def list_tasks_for_investigation(
    investigation_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Offset index"),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    items, total = service.list_tasks_for_investigation(
        investigation_id=investigation_id,
        limit=limit,
        offset=offset,
    )
    return TaskListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
