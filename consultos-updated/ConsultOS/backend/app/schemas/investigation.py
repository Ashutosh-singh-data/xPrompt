from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.investigation import InvestigationStatus
from app.schemas.common import PaginatedResponse


class InvestigationCreate(BaseModel):
    """Schema for creating a new business investigation."""

    business_question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The business inquiry or strategic question to investigate.",
    )

    @field_validator("business_question")
    @classmethod
    def validate_business_question(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("business_question must not be empty or whitespace-only.")
        return trimmed


class InvestigationRead(BaseModel):
    """Schema for returning an investigation."""

    id: str
    business_question: str
    status: InvestigationStatus
    current_plan_version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationListResponse(PaginatedResponse[InvestigationRead]):
    """Paginated list of investigations."""
    pass
