from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.common import PaginatedResponse


class EvidenceRead(BaseModel):
    """Schema for evidence collected in an investigation."""

    id: str
    investigation_id: str
    task_id: Optional[str] = None
    source_type: str
    source_reference: str
    finding: str
    supporting_data: Optional[Any] = None
    verification_status: str = "unverified"
    verification_metadata: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(PaginatedResponse[EvidenceRead]):
    """Paginated list of evidence records."""
    pass
