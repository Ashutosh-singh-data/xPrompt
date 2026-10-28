from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class FinalReportRead(BaseModel):
    """Schema for a finalized investigation report."""

    id: str
    investigation_id: str
    version: int
    executive_summary: str
    findings: Any
    recommendations: Any
    limitations: Any
    unresolved_questions: Any
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
