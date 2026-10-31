
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from backend.database import init_db

from backend.models.schemas import (
    InvestigationCreate
)

from backend.models.investigation import (
    create_investigation,
    get_investigation,
    list_investigations,
    get_investigation_events
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize database when server starts
    init_db()

    print("ConsultOS database initialized.")

    yield

    print("ConsultOS shutting down.")


app = FastAPI(
    title="ConsultOS",
    description="Autonomous Business Investigation Platform",
    version="0.2.0",
    lifespan=lifespan
)


@app.get("/")
def home():

    return {
        "application": "ConsultOS",
        "message": "Business Investigation Platform is running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "database": "initialized",
        "version": "0.2.0"
    }


@app.post("/investigations")
def create_new_investigation(
    request: InvestigationCreate
):

    investigation = create_investigation(
        question=request.question,
        title=request.title
    )

    return {
        "message": "Investigation created successfully",
        "investigation": investigation
    }


@app.get("/investigations")
def get_all_investigations():

    return {
        "investigations": list_investigations()
    }


@app.get("/investigations/{investigation_id}")
def get_one_investigation(
    investigation_id: str
):

    investigation = get_investigation(
        investigation_id
    )

    if not investigation:

        raise HTTPException(
            status_code=404,
            detail="Investigation not found"
        )

    return investigation


@app.get("/investigations/{investigation_id}/events")
def get_events(
    investigation_id: str
):

    investigation = get_investigation(
        investigation_id
    )

    if not investigation:

        raise HTTPException(
            status_code=404,
            detail="Investigation not found"
        )

    return {
        "events": get_investigation_events(
            investigation_id
        )
    }
