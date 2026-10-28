import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
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


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Explicit association table for task dependencies
task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column(
        "task_id",
        String(36),
        ForeignKey("investigation_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "depends_on_task_id",
        String(36),
        ForeignKey("investigation_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    CheckConstraint(
        "task_id != depends_on_task_id",
        name="ck_task_no_self_dependency",
    ),
)


class InvestigationTask(Base):
    """InvestigationTask persistent entity representing an analytical or workflow unit."""

    __tablename__ = "investigation_tasks"

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
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    task_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TaskStatus.PENDING.value,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    result: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
    )
    error: Mapped[Optional[Any]] = mapped_column(
        JSON,
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
        back_populates="tasks",
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        back_populates="task",
    )

    # Tasks that this task depends on (must complete before this task)
    dependencies: Mapped[List["InvestigationTask"]] = relationship(
        "InvestigationTask",
        secondary=task_dependencies,
        primaryjoin="InvestigationTask.id == task_dependencies.c.task_id",
        secondaryjoin="InvestigationTask.id == task_dependencies.c.depends_on_task_id",
        back_populates="dependents",
    )

    # Tasks that depend on this task
    dependents: Mapped[List["InvestigationTask"]] = relationship(
        "InvestigationTask",
        secondary=task_dependencies,
        primaryjoin="InvestigationTask.id == task_dependencies.c.depends_on_task_id",
        secondaryjoin="InvestigationTask.id == task_dependencies.c.task_id",
        back_populates="dependencies",
    )

    @property
    def dependency_ids(self) -> List[str]:
        """Return list of task IDs that this task depends on."""
        return [dep.id for dep in self.dependencies] if self.dependencies else []

    __table_args__ = (
        CheckConstraint("attempts >= 0", name="ck_task_attempts_nonnegative"),
        Index("ix_tasks_inv_status", "investigation_id", "status"),
    )
