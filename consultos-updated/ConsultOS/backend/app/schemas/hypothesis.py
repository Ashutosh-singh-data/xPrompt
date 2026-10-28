from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.hypothesis import HypothesisStatus
from app.schemas.common import PaginatedResponse


class HypothesisRead(BaseModel):
    """Schema for an investigation hypothesis."""

    id: str
    investigation_id: str
    statement: str
    status: HypothesisStatus
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HypothesisListResponse(PaginatedResponse[HypothesisRead]):
    """Paginated list of hypotheses."""
    pass
