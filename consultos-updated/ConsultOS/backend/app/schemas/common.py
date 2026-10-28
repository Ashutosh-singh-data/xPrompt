from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Overall application status (healthy/unhealthy)")
    app_name: str = Field(..., description="Application name")
    database: str = Field(..., description="Database connection status (connected/disconnected)")

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T] = Field(..., description="List of items for current page")
    total: int = Field(..., ge=0, description="Total number of items available")
    limit: int = Field(..., ge=1, description="Items per page limit")
    offset: int = Field(..., ge=0, description="Items offset")

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Structured error details."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")
    details: Optional[Any] = Field(default=None, description="Optional supplemental context")


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: ErrorDetail
