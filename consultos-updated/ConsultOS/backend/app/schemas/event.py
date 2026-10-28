from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.common import PaginatedResponse


class InvestigationEventRead(BaseModel):
    """Schema for an investigation audit/timeline event."""

    id: str
    investigation_id: str
    task_id: Optional[str] = None
    event_type: str
    details: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(PaginatedResponse[InvestigationEventRead]):
    """Paginated list of investigation events."""
    pass
