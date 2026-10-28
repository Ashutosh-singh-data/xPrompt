import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.hypothesis import hypothesis_evidence

if TYPE_CHECKING:
    from app.models.investigation import Investigation
    from app.models.task import InvestigationTask
    from app.models.hypothesis import Hypothesis


class EvidenceVerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(Base):
    """Evidence persistent entity representing a verified fact or finding."""

    __tablename__ = "evidence"

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
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("investigation_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="document",
        index=True,
    )
    source_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    finding: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    supporting_data: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=EvidenceVerificationStatus.UNVERIFIED.value,
        index=True,
    )
    verification_metadata: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
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
        back_populates="evidence",
    )
    task: Mapped[Optional["InvestigationTask"]] = relationship(
        "InvestigationTask",
        back_populates="evidence",
    )
    hypotheses: Mapped[List["Hypothesis"]] = relationship(
        "Hypothesis",
        secondary=hypothesis_evidence,
        back_populates="evidence",
    )

    __table_args__ = (
        Index("ix_evidence_inv_created", "investigation_id", "created_at"),
    )


from sqlalchemy import event, select
from app.core.exceptions import InvalidRelationshipException


@event.listens_for(Evidence, "before_insert")
@event.listens_for(Evidence, "before_update")
def validate_evidence_task_same_investigation(mapper, connection, target: Evidence):
    """Enforce that an evidence task belongs to the same investigation as the evidence."""
    if target.task_id is not None:
        from app.models.task import InvestigationTask

        if target.task is not None and target.task.investigation_id != target.investigation_id:
            raise InvalidRelationshipException(
                "Evidence task must belong to the same investigation as the evidence.",
                details={
                    "evidence_investigation_id": target.investigation_id,
                    "task_investigation_id": target.task.investigation_id,
                },
            )

        stmt = select(InvestigationTask.investigation_id).where(
            InvestigationTask.id == target.task_id
        )
        task_inv_id = connection.execute(stmt).scalar()
        if task_inv_id is not None and task_inv_id != target.investigation_id:
            raise InvalidRelationshipException(
                "Evidence task must belong to the same investigation as the evidence.",
                details={
                    "evidence_investigation_id": target.investigation_id,
                    "task_investigation_id": task_inv_id,
                },
            )

