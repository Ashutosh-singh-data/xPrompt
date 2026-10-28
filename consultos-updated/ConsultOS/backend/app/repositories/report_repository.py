from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.report import FinalReport


class ReportRepository:
    """Repository handling persistent storage and retrieval of FinalReport entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, report: FinalReport) -> FinalReport:
        """Add report to active session."""
        self.db.add(report)
        return report

    def get_latest_by_investigation(self, investigation_id: str) -> Optional[FinalReport]:
        """Retrieve the latest finalized report for an investigation, if one exists."""
        stmt = (
            select(FinalReport)
            .where(FinalReport.investigation_id == investigation_id)
            .order_by(FinalReport.version.desc(), FinalReport.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()
