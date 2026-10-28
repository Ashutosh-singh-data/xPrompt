from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.report_service import ReportService
from app.schemas.report import FinalReportRead

router = APIRouter(prefix="/investigations", tags=["Reports"])


@router.get(
    "/{investigation_id}/report",
    response_model=FinalReportRead,
    summary="Get Final Report",
    description="Retrieve the latest synthesis report for an investigation.",
)
def get_report_for_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.get_report_for_investigation(investigation_id)


@router.post(
    "/{investigation_id}/report",
    response_model=FinalReportRead,
    summary="Generate Final Report",
    description="Synthesize verified findings, hypothesis statuses, and evidence-backed recommendations into a final report.",
)
def generate_report_for_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.generate_report(investigation_id)

