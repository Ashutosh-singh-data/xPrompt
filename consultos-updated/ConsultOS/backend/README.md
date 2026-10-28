# ConsultOS Backend — Parts 1, 2 & 3: Foundation, Investigation Engine & Intelligence Reliability

ConsultOS is an Autonomous Business Investigation & Workflow Platform.
- **Part 1**: Establishes the production-grade persistent data foundation, repository and service boundaries, database integrity constraints, and core REST API layer.
- **Part 2**: Implements the analytical investigation planning engine, DAG dependency graph, approved analytical tool registry, task executor, orchestrator, and Part 1 database integration adapter.
- **Part 3**: Implements investigation intelligence and reliability: rule-based evidence verification, hypothesis evaluation, bounded failure recovery with backoff, dynamic replanning with deduplication, audit event streams, and evidence-backed synthesis reports.

---

## 1. Overview

ConsultOS accepts high-level business questions (e.g. *"Why did our sales decline last month?"*) and analytical datasets, formulates testable hypotheses, builds dependency-aware task graphs, executes approved analytical tools, extracts verified evidence, and maintains persistent execution audit trails.

### Core Capabilities

#### Part 1: Production-Grade Foundation
- **Persistent Data Models**: Full relational schema across Investigations, Tasks, Hypotheses, Evidence, Events, and Reports using modern SQLAlchemy 2.x mapped-column style.
- **Relational Integrity**: Foreign key enforcement, cascading cleanup, task self-dependency rejection, and cross-investigation relationship validation.
- **Layered Architecture**: Strict separation between API routes, domain services, data repositories, and persistent models.
- **Transaction Atomicity**: Atomic creation of investigations alongside their audit timeline events with automatic rollback on error.
- **Schema Validation**: Pydantic v2 schemas for all request/response models with pagination, whitespace stripping, and length constraints.
- **Isolated Automated Testing**: In-memory SQLite test suite with clean session fixtures and table truncation between runs.

#### Part 2: Investigation Planning & Execution Engine
- **Deterministic Rule-Based Planner**: Analyzes question intent, detects metrics, dimensions, and temporal intervals, and generates only supported hypotheses and tasks without hallucinating non-existent columns. Rejects unsupported inquiries.
- **Plan Validator**: Validates task/hypothesis uniqueness, verifies tool registry membership and parameter schemas, checks dependency references, enforces task limits ($\le 50$), and detects circular dependency graphs upfront.
- **DAG Dependency Graph**: Manages task dependencies, performs deterministic topological sorting, resolves ready tasks, and dynamically blocks downstream tasks if an upstream prerequisite fails.
- **Approved Analytical Tool Registry**:
  1. `dataset_profiler`: Row counts, column types, missing value percentages, unique counts, duplicate rows, and statistical distributions.
  2. `data_validator`: Null checks, duplicate detection, and non-negative metric constraint validation.
  3. `grouped_aggregator`: Grouped and overall aggregations (`sum`, `mean`, `median`, `min`, `max`, `count`, `std`) across dimensions.
  4. `timeseries_analyzer`: Periodic aggregation, period-over-period percentage changes, trend detection, and missing period detection.
- **Task Executor & Orchestrator**: Executes tasks sequentially in topological order, enforces output limits, captures execution durations in milliseconds, blocks dependent tasks on failure, continues independent branches safely, and guarantees failed tasks are never marked as completed.
- **Part 1 Integration Adapter**: Bridges in-memory engine objects with persistent SQLAlchemy models. Automatically persists planned tasks and hypotheses, tracks task lifecycle (`pending` $\rightarrow$ `completed`/`failed`/`blocked`), generates verified `Evidence` records from tool outputs, logs audit `InvestigationEvent`s, and transitions investigation status to `completed` or `failed`.

---

## 2. Architecture and Module Responsibilities

The backend follows a layered, decoupled service-repository and engine architecture:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Application entry point, lifespan, CORS, and global error handlers
│   ├── core/                    # Foundation core
│   │   ├── __init__.py
│   │   ├── config.py            # Centralized settings via pydantic-settings (.env support)
│   │   ├── database.py          # SQLAlchemy 2.x engine, sessionmaker, SQLite PRAGMA configuration
│   │   └── exceptions.py        # Domain exceptions (NotFound, NotReady, InvalidRelationship, etc.)
│   ├── api/                     # REST API layer
│   │   ├── __init__.py
│   │   ├── router.py            # Unified API router mounting all route controllers
│   │   └── routes/              # Route controllers
│   │       ├── __init__.py
│   │       ├── health.py        # GET /api/health (with active DB ping)
│   │       ├── investigations.py# Investigation CRUD + Planning & Execution endpoints
│   │       ├── tasks.py         # GET /api/investigations/{id}/tasks
│   │       ├── evidence.py      # GET /api/investigations/{id}/evidence
│   │       ├── events.py        # GET /api/investigations/{id}/events
│   │       └── reports.py       # GET /api/investigations/{id}/report
│   ├── models/                  # SQLAlchemy 2.x ORM entities
│   │   ├── __init__.py
│   │   ├── investigation.py     # Investigation lifecycle model
│   │   ├── task.py              # InvestigationTask & task_dependencies association table
│   │   ├── hypothesis.py        # Hypothesis & hypothesis_evidence association table
│   │   ├── evidence.py          # Evidence with cross-investigation validation
│   │   ├── event.py             # InvestigationEvent audit log
│   │   └── report.py            # FinalReport deliverables
│   ├── schemas/                 # Pydantic v2 DTO schemas
│   │   ├── __init__.py
│   │   ├── common.py            # Pagination, HealthResponse, ErrorDetail, ErrorResponse
│   │   ├── investigation.py     # InvestigationCreate, InvestigationRead, InvestigationListResponse
│   │   ├── task.py              # TaskRead, TaskListResponse
│   │   ├── hypothesis.py        # HypothesisRead, HypothesisListResponse
│   │   ├── evidence.py          # EvidenceRead, EvidenceListResponse
│   │   ├── event.py             # InvestigationEventRead, EventListResponse
│   │   └── report.py            # FinalReportRead
│   ├── repositories/            # Data Access Layer (persistence, raw queries, counts)
│   │   ├── __init__.py
│   │   ├── investigation_repository.py
│   │   ├── task_repository.py
│   │   ├── evidence_repository.py
│   │   ├── event_repository.py
│   │   └── report_repository.py
│   ├── services/                # Business Domain Layer (transactions, business logic)
│   │   ├── __init__.py
│   │   ├── investigation_service.py
│   │   ├── task_service.py
│   │   ├── evidence_service.py
│   │   ├── event_service.py
│   │   └── report_service.py
│   └── engine/                  # Part 2: Planning & Execution Engine
│       ├── __init__.py
│       ├── schemas.py           # InvestigationPlan, PlannedTask, ExecutionSummary, etc.
│       ├── planner.py           # RuleBasedPlanner analyzing questions & columns
│       ├── validator.py         # PlanValidator enforcing uniqueness, tools, cycles, limits
│       ├── graph.py             # DependencyGraph (DAG topological sort, cycle detection, blocking)
│       ├── executor.py          # TaskExecutor enforcing tool resolution, validation & limits
│       ├── orchestrator.py      # InvestigationOrchestrator coordinating dependency execution
│       ├── adapter.py           # InvestigationEngineAdapter bridging engine outcomes to DB
│       └── tools/               # Analytical Tool Registry and implementations
│           ├── __init__.py
│           ├── base.py          # BaseTool abstract class
│           ├── registry.py      # Centralized ToolRegistry
│           ├── profiling.py     # DatasetProfilingTool
│           ├── validation.py    # DataValidationTool
│           ├── aggregation.py   # GroupedAggregationTool
│           └── timeseries.py    # TimeSeriesAnalysisTool
├── tests/                       # Automated Pytest suite (53 tests)
│   ├── conftest.py              # In-memory SQLite fixture, session management, TestClient
│   ├── test_health.py           # Health check and database ping verification
│   ├── test_investigations.py   # Investigation creation, validation, pagination, 404s
│   ├── test_tasks.py            # Task listing, dependency IDs, investigation isolation
│   ├── test_evidence.py         # Evidence listing, cross-investigation isolation
│   ├── test_events.py           # Event persistence and audit ordering
│   ├── test_reports.py          # Report retrieval, not-ready handling, 404s
│   ├── test_database_integrity.py # Foreign keys, self-dependency checks, cascade delete
│   ├── test_planner.py          # Planner rules, unsupported questions, column verification
│   ├── test_plan_validator.py   # Schema validation, cycle detection, tool parameter validation
│   ├── test_dependency_graph.py # Topological ordering, cycle detection, ready/blocked states
│   ├── test_analytical_tools.py # Profiling, validation, aggregation, and time-series tools
│   ├── test_executor_and_orchestrator.py # Multi-task run, branch failure, independent continuation
│   └── test_part2_integration.py# End-to-end plan preview, validation, execution, DB persistence
├── pytest.ini                   # Pytest configuration with pythonpath
├── requirements.txt             # Locked project dependencies
├── .env.example                 # Environment variable template
├── .gitignore                   # Ignore rules for virtual environment, DB, cache
└── README.md                    # Documentation
```

---

## 3. Prerequisites

- **Python**: Version 3.11, 3.12, 3.13, or 3.14 (Verified working on Python 3.14 on Windows).
- **PowerShell** or equivalent shell on Windows.
- **Git** (optional).

---

## 4. Virtual Environment Setup on Windows PowerShell

From the repository root (`d:\ConsultOS`):

```powershell
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

If script execution is disabled in PowerShell, enable it for the current process:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

---

## 5. Dependency Installation

With the virtual environment activated:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Installed packages:
- `fastapi`: Modern, fast web framework for building APIs.
- `uvicorn[standard]`: Production-grade ASGI web server.
- `pydantic` & `pydantic-settings`: Data validation, serialization, and settings management.
- `sqlalchemy`: 2.x Object Relational Mapper and SQL toolkit.
- `pandas`: Tabular data analysis and transformation for approved analytical tools.
- `pytest`: Automated test runner and assertion framework.
- `httpx`: HTTP client for FastAPI `TestClient`.
- `python-dotenv`: Environment configuration support.

---

## 6. Environment Configuration

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

### Configuration Variables
| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `ConsultOS Backend` | Displayed in health response and API docs |
| `API_PREFIX` | `/api` | Root path prefix for all REST endpoints |
| `DEBUG` | `false` | Enables SQLAlchemy SQL echo and verbose logging |
| `DATABASE_URL` | `sqlite:///{BACKEND_DIR}/data/consultos.db` | Absolute path to SQLite database file |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://127.0.0.1:5173"]` | Allowed CORS origins (e.g. Vite frontend) |

The SQLite database path is resolved to an absolute path (`backend/data/consultos.db`) by default. Parent directories are created automatically if they do not exist.

---

## 7. Database Initialization Behavior

Database tables are initialized automatically during application startup via the FastAPI `lifespan` handler (`init_db(engine)`).
- Tables created: `investigations`, `investigation_tasks`, `task_dependencies`, `hypotheses`, `hypothesis_evidence`, `evidence`, `investigation_events`, `final_reports`.
- SQLite foreign key constraints are explicitly enabled upon connection (`PRAGMA foreign_keys=ON;`).

---

## 8. Backend Startup Commands

From the `backend` directory with the virtual environment activated:

```powershell
# Start Uvicorn development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

If port 8000 is occupied by another local service:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

---

## 9. API Documentation Location

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 10. Available REST Endpoints

All endpoints are prefixed with `/api`.

### Health
- `GET /api/health`: Returns application status and database connectivity status (`connected` / `disconnected`).

### Investigations (Part 1 CRUD)
- `POST /api/investigations`: Creates a new business inquiry and records initial draft event.
- `GET /api/investigations?limit=20&offset=0`: Returns paginated list of investigations ordered newest first.
- `GET /api/investigations/{investigation_id}`: Returns investigation details or 404.

### Investigation Planning & Execution (Part 2 Engine)
- `POST /api/investigations/plan/preview`:
  - Input: `{"business_question": "string", "columns": ["string"], "data": [{...}]}`.
  - Deterministically generates an `InvestigationPlan` (hypotheses, tasks, tool parameters, dependencies) without persisting to DB.
- `POST /api/investigations/plan/validate`:
  - Input: `{"plan": {...}, "available_columns": ["string"]}`.
  - Validates structural and relational integrity, returning `PlanValidationResult(is_valid, errors, warnings)`.
- `POST /api/investigations/{investigation_id}/plan`:
  - Generates an investigation plan and persists hypotheses, tasks, and dependency associations into the database.
- `POST /api/investigations/{investigation_id}/execute`:
  - Input: `{"data": [{...}]}`.
  - Executes the plan using the DAG orchestrator, updates DB tasks (`completed`, `failed`, `blocked`), extracts verified `Evidence`, logs timeline events, and transitions investigation status to `completed` or `failed`. Returns `ExecutionSummary`.

### Tasks, Evidence, Events, and Reports
- `GET /api/investigations/{investigation_id}/tasks`: Returns tasks belonging to the investigation, including associated `dependency_ids`, status, results, and errors.
- `GET /api/investigations/{investigation_id}/evidence`: Returns verified evidence artifacts extracted by tools during plan execution.
- `GET /api/investigations/{investigation_id}/events`: Returns chronological audit events (`investigation_created`, `plan_generated`, `task_completed`, `investigation_execution_finished`).
- `GET /api/investigations/{investigation_id}/report`: Returns latest finalized report or `404 Not Found` with `REPORT_NOT_READY`.

---

## 11. Test Commands

Automated tests run against an isolated in-memory SQLite database (`sqlite:///:memory:`) using FastAPI `TestClient`.

From the `backend` directory:

```powershell
# Run all tests with verbose output
.\.venv\Scripts\pytest -v

# Run with summary
.\.venv\Scripts\pytest -q

# Run specific Part 3 test suites
.\.venv\Scripts\pytest tests/test_part3_verification.py tests/test_part3_hypotheses.py tests/test_part3_recovery.py tests/test_part3_replanning.py tests/test_part3_reports.py tests/test_part3_end_to_end.py -v
```

### Complete Test Suite Summary (75 Tests)
- `test_health.py` (2 tests): Verifies healthy and database failure responses.
- `test_investigations.py` (6 tests): Validates creation, empty question rejection, whitespace rejection, single item retrieval, 404s, pagination, and event persistence.
- `test_tasks.py` (3 tests): Validates task listing, empty list, 404 on missing investigation, dependency IDs, and cross-investigation isolation.
- `test_evidence.py` (3 tests): Validates evidence listing, empty list, 404s, and cross-investigation isolation.
- `test_events.py` (3 tests): Validates event persistence, chronological ordering, and cross-investigation isolation.
- `test_reports.py` (3 tests): Validates report retrieval, not-ready behavior when absent, and 404 for unknown investigations.
- `test_database_integrity.py` (7 tests): Validates non-null constraints, task attempts >= 0, hypothesis confidence range (0.0 to 1.0), task self-dependency rejection, foreign keys, cascading deletion, and invalid cross-investigation evidence-to-task rejection.
- `test_planner.py` (5 tests): Validates sales decline hypothesis & task generation, column verification (no hallucination), empty question rejection, empty columns rejection, and unsupported inquiry rejection.
- `test_plan_validator.py` (7 tests): Validates valid plan approval, duplicate task/hypothesis ID rejection, unregistered tool rejection, parameter validation, missing dependency rejection, cycle detection, and task limit enforcement.
- `test_dependency_graph.py` (4 tests): Validates deterministic topological sort, cycle detection with cycle path, ready task progression, and downstream blocked task identification on failure.
- `test_analytical_tools.py` (4 tests): Verifies `dataset_profiler`, `data_validator`, `grouped_aggregator`, and `timeseries_analyzer` under normal data, empty data, and constraint violation scenarios.
- `test_executor_and_orchestrator.py` (3 tests): Validates sequential DAG orchestration, downstream dependency blocking, independent branch continuation, and strict failure status enforcement.
- `test_part2_integration.py` (3 tests): End-to-end API testing of plan preview, plan validation, and plan execution with database persistence of tasks, evidence, and events.
- `test_part3_verification.py` (5 tests): Rule-based evidence verification, non-completed task rejection, finding contradiction rejection, empty dataset handling, and multi-evidence contradiction detection.
- `test_part3_hypotheses.py` (4 tests): Evaluates hypotheses against verified evidence, contradictory clean data evaluation, insufficient evidence handling, and hypothesis-evidence linking.
- `test_part3_recovery.py` (5 tests): Retryable vs non-retryable error classification, bounded retry recovery with exponential backoff, immediate parameter error abort, retry limits enforcement, and successful result preservation.
- `test_part3_replanning.py` (4 tests): Dynamic replanning trigger on task failure, duplicate-task prevention via signature hashing, iteration and total task limit enforcement, and data quality trigger handling.
- `test_part3_reports.py` (2 tests): Final synthesis report generation with verified facts, unresolved questions, limitations, evidence-backed recommendations, and GET/POST API endpoints.
- `test_part3_end_to_end.py` (2 tests): Full autonomous investigation lifecycle (business question $\rightarrow$ execution $\rightarrow$ verification $\rightarrow$ evaluation $\rightarrow$ report) and automated recovery/replanning on failure.

---

## 12. Current Implementation Status

Parts 1, 2, and 3 are fully implemented:
- **Part 1**: Foundation, database models, repository layer, services, REST API, integrity constraints, and isolated test harness.
- **Part 2**: Deterministic planner, tool registry, dependency graph (DAG), task executor, and orchestrator adapter.
- **Part 3**: Evidence verification service, hypothesis evaluation engine, bounded failure recovery with backoff, dynamic replanning with deduplication, audit event streams, and evidence-backed synthesis reporting.

---

## 13. Known Limitations

- **Authentication**: Endpoints remain unauthenticated for local development and benchmarking.
- **Planner Scope**: Uses deterministic rule-based column and keyword analysis. Highly abstract inquiries without matching numeric/dimensional columns are flagged as unsupported.
- **Execution Mode**: Executes analytical tasks in topological order. Bounded concurrent worker execution can be configured for distributed enterprise deployments.
