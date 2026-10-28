from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.evidence_service import EvidenceService
from app.schemas.evidence import EvidenceListResponse

router = APIRouter(prefix="/investigations", tags=["Evidence"])


@router.get(
    "/{investigation_id}/evidence",
    response_model=EvidenceListResponse,
    summary="List Investigation Evidence",
    description="Retrieve evidence artifacts associated strictly with the requested investigation.",
)
def list_evidence_for_investigation(
    investigation_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Offset index"),
    db: Session = Depends(get_db),
):
    service = EvidenceService(db)
    items, total = service.list_evidence_for_investigation(
        investigation_id=investigation_id,
        limit=limit,
        offset=offset,
    )
    return EvidenceListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
