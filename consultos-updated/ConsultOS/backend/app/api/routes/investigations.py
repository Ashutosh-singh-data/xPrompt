from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
import pandas as pd

from app.core.database import get_db
from app.services.investigation_service import InvestigationService
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationRead,
    InvestigationListResponse,
)
from app.engine.schemas import (
    InvestigationPlan,
    PlanValidationResult,
    ExecutionSummary,
    PlanPreviewRequest,
    PlanValidationRequest,
    ExecutionRequest,
)
from app.engine.planner import rule_based_planner
from app.engine.validator import plan_validator
from app.engine.adapter import engine_adapter

router = APIRouter(prefix="/investigations", tags=["Investigations"])


# --- Engine Routes (Static routes before variable {investigation_id}) ---

@router.post(
    "/plan/preview",
    response_model=InvestigationPlan,
    summary="Preview Investigation Plan",
    description="Deterministically generates hypotheses and tasks for a business question and dataset without persisting.",
)
def preview_plan(payload: PlanPreviewRequest):
    """Generate an analytical investigation plan without persistence."""
    df = pd.DataFrame(payload.data) if payload.data else None
    columns = payload.columns
    if not columns and df is not None:
        columns = list(df.columns)

    return rule_based_planner.plan(
        business_question=payload.business_question,
        columns=columns,
        dataset_profile=payload.dataset_profile,
        df=df,
    )


@router.post(
    "/plan/validate",
    response_model=PlanValidationResult,
    summary="Validate Investigation Plan",
    description="Validates tasks, dependencies, cycles, tool registry parameters, and hypothesis references.",
)
def validate_plan(payload: PlanValidationRequest):
    """Validate structural and relational integrity of an investigation plan."""
    return plan_validator.validate(
        plan=payload.plan,
        available_columns=payload.available_columns,
    )


# --- Core Investigation CRUD Routes ---

@router.post(
    "",
    response_model=InvestigationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Investigation",
    description="Create a new business inquiry and persist initial draft state and creation audit event.",
)
def create_investigation(
    payload: InvestigationCreate,
    db: Session = Depends(get_db),
):
    service = InvestigationService(db)
    investigation = service.create_investigation(business_question=payload.business_question)
    return investigation


@router.get(
    "",
    response_model=InvestigationListResponse,
    summary="List Investigations",
    description="Retrieve paginated list of investigations ordered newest first.",
)
def list_investigations(
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Offset index"),
    db: Session = Depends(get_db),
):
    service = InvestigationService(db)
    items, total = service.list_investigations(limit=limit, offset=offset)
    return InvestigationListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{investigation_id}",
    response_model=InvestigationRead,
    summary="Get Investigation",
    description="Retrieve a single investigation by unique identifier.",
)
def get_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
):
    service = InvestigationService(db)
    return service.get_investigation(investigation_id)


# --- Investigation Engine Execution Routes ---

@router.post(
    "/{investigation_id}/plan",
    response_model=InvestigationPlan,
    summary="Generate and Persist Plan",
    description="Generates an investigation plan and persists hypotheses and tasks to the database.",
)
def generate_and_persist_plan(
    investigation_id: str,
    payload: Optional[PlanPreviewRequest] = None,
    db: Session = Depends(get_db),
):
    service = InvestigationService(db)
    investigation = service.get_investigation(investigation_id)

    q = payload.business_question if (payload and payload.business_question) else investigation.business_question
    df = pd.DataFrame(payload.data) if (payload and payload.data) else None
    cols = payload.columns if (payload and payload.columns) else (list(df.columns) if df is not None else None)
    profile = payload.dataset_profile if payload else None

    plan = rule_based_planner.plan(
        business_question=q,
        columns=cols,
        dataset_profile=profile,
        df=df,
    )
    engine_adapter.persist_plan(investigation_id=investigation.id, plan=plan, db=db)
    return plan


@router.post(
    "/{investigation_id}/execute",
    response_model=ExecutionSummary,
    summary="Execute Investigation Plan",
    description="Executes planned analytical tasks on the provided dataset, records execution events, and persists evidence.",
)
def execute_investigation(
    investigation_id: str,
    payload: ExecutionRequest,
    db: Session = Depends(get_db),
):
    service = InvestigationService(db)
    investigation = service.get_investigation(investigation_id)

    # Convert data rows to DataFrame
    df = pd.DataFrame(payload.data)
    cols = list(df.columns)

    # Generate plan from investigation business question and available columns
    plan = rule_based_planner.plan(
        business_question=investigation.business_question,
        columns=cols,
        df=df,
    )

    # Execute plan, update task statuses, persist evidence and events
    summary = engine_adapter.execute_and_persist(
        investigation_id=investigation.id,
        plan=plan,
        data=df,
        db=db,
    )
    return summary
