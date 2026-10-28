import uuid
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FinalReport(Base):
    """FinalReport persistent entity representing the synthesis and evidence-backed deliverables."""

    __tablename__ = "final_reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    executive_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    findings: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    recommendations: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    limitations: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    unresolved_questions: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        index=True,
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="reports",
    )

    __table_args__ = (
        Index("ix_reports_inv_created", "investigation_id", "created_at"),
    )
