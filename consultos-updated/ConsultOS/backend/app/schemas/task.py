from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.task import TaskStatus
from app.schemas.common import PaginatedResponse


class TaskRead(BaseModel):
    """Schema for an investigation task."""

    id: str
    investigation_id: str
    title: str
    description: Optional[str] = None
    task_type: str
    status: TaskStatus
    attempts: int
    result: Optional[Any] = None
    error: Optional[Any] = None
    dependency_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(PaginatedResponse[TaskRead]):
    """Paginated list of investigation tasks."""
    pass
