
from pydantic import BaseModel, Field
from typing import Optional


class InvestigationCreate(BaseModel):

    question: str = Field(
        min_length=10,
        max_length=2000,
        description="Business question to investigate"
    )

    title: Optional[str] = Field(
        default=None,
        max_length=150
    )


class InvestigationResponse(BaseModel):

    id: str
    title: str
    question: str
    status: str
    created_at: str
    updated_at: str
