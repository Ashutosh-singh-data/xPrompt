# ConsultOS — Autonomous Business Investigation & Workflow Platform

ConsultOS is an autonomous business investigation and workflow platform that accepts high-level business questions, decomposes them into structured hypotheses and analytical tasks, collects evidence, and generates verified executive reports.

## Project Structure

- `backend/`: Production-grade FastAPI, SQLAlchemy 2.x, Pydantic v2, and Analytical Planning/Execution Engine.
  - **Part 1**: Persistent relational models, repositories, services, and core REST API.
  - **Part 2**: Deterministic rule-based planner, plan validator, DAG dependency graph, analytical tools (`dataset_profiler`, `data_validator`, `grouped_aggregator`, `timeseries_analyzer`), task executor, orchestrator, and database integration adapter.
  - See [backend/README.md](backend/README.md) for full documentation, endpoints, architecture, and test instructions.
- `frontend/`: (Reserved for future frontend application).

## Quick Start (Backend)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env

# Run all 53 automated tests
pytest -v

# Run backend development server
python -m uvicorn app.main:app --reload
```
