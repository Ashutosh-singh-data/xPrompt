import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Table,
    Column,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation
    from app.models.evidence import Evidence


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


hypothesis_evidence = Table(
    "hypothesis_evidence",
    Base.metadata,
    Column(
        "hypothesis_id",
        String(36),
        ForeignKey("hypotheses.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "evidence_id",
        String(36),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Hypothesis(Base):
    """Hypothesis persistent entity representing a testable assertion."""

    __tablename__ = "hypotheses"

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
    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=HypothesisStatus.PROPOSED.value,
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
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
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="hypotheses",
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        secondary=hypothesis_evidence,
        back_populates="hypotheses",
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_hypothesis_confidence_range",
        ),
        Index("ix_hypotheses_inv_status", "investigation_id", "status"),
    )
