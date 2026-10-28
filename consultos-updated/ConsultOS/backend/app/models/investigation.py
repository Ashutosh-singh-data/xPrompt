import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.task import InvestigationTask
    from app.models.hypothesis import Hypothesis
    from app.models.evidence import Evidence
    from app.models.event import InvestigationEvent
    from app.models.report import FinalReport


class InvestigationStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Investigation(Base):
    """Investigation persistent entity representing a business inquiry workflow."""

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    business_question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=InvestigationStatus.DRAFT.value,
        index=True,
    )
    current_plan_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
    )

    # Relationships
    tasks: Mapped[List["InvestigationTask"]] = relationship(
        "InvestigationTask",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationTask.created_at",
    )
    hypotheses: Mapped[List["Hypothesis"]] = relationship(
        "Hypothesis",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="Hypothesis.created_at",
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="Evidence.created_at",
    )
    events: Mapped[List["InvestigationEvent"]] = relationship(
        "InvestigationEvent",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationEvent.created_at",
    )
    reports: Mapped[List["FinalReport"]] = relationship(
        "FinalReport",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="FinalReport.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_investigations_status_created", "status", "created_at"),
    )
