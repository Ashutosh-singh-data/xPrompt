from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DatasetColumnProfile(BaseModel):
    """Profile metadata for an individual dataset column."""

    name: str = Field(..., description="Column header name")
    dtype: str = Field(..., description="Inferred data type (e.g. integer, float, string, datetime)")
    sample_values: List[Any] = Field(default_factory=list, description="Sample values from the column")
    nullable: bool = Field(default=True, description="Whether column contains nulls")
    unique_count: Optional[int] = Field(default=None, description="Number of distinct values")


class DatasetProfile(BaseModel):
    """Metadata profile representing a tabular dataset."""

    name: str = Field(default="dataset", description="Identifier or name of dataset")
    row_count: int = Field(default=0, ge=0, description="Total number of rows")
    columns: List[str] = Field(..., description="List of column names")
    dtypes: Dict[str, str] = Field(default_factory=dict, description="Column name to dtype mapping")
    column_profiles: List[DatasetColumnProfile] = Field(default_factory=list)
    sample_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Sample records for inspection")


class PlannedHypothesis(BaseModel):
    """A testable assertion generated during the planning phase."""

    id: str = Field(..., description="Unique identifier for the hypothesis (e.g. hyp_1)")
    statement: str = Field(..., description="Testable statement formulated from the question and data")
    rationale: str = Field(..., description="Explanation of why this hypothesis is relevant to the question")

    model_config = ConfigDict(from_attributes=True)


class PlannedTask(BaseModel):
    """An analytical task specification within an investigation plan."""

    id: str = Field(..., description="Unique task identifier (e.g. task_1)")
    title: str = Field(..., description="Concise task title")
    description: Optional[str] = Field(default=None, description="Detailed instructions or goal")
    task_type: str = Field(default="analysis", description="Category of task (e.g. profiling, validation, analysis)")
    tool_name: str = Field(..., description="Approved analytical tool to invoke")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Validated parameters passed to the tool")
    dependency_ids: List[str] = Field(default_factory=list, description="IDs of tasks that must succeed before this task")
    hypothesis_id: Optional[str] = Field(default=None, description="Linked hypothesis ID, if applicable")

    model_config = ConfigDict(from_attributes=True)


class InvestigationPlan(BaseModel):
    """A structured, dependency-aware analytical investigation plan."""

    plan_id: str = Field(..., description="Unique plan identifier")
    business_question: str = Field(..., description="The business question being investigated")
    dataset_name: Optional[str] = Field(default="primary_dataset", description="Target dataset name")
    hypotheses: List[PlannedHypothesis] = Field(default_factory=list, description="Formulated hypotheses")
    tasks: List[PlannedTask] = Field(default_factory=list, description="Tasks to execute")
    created_at: datetime = Field(default_factory=get_utc_now)

    model_config = ConfigDict(from_attributes=True)


class PlanValidationResult(BaseModel):
    """Result of structural and relational plan validation."""

    is_valid: bool = Field(..., description="True if plan satisfies all validation rules")
    errors: List[str] = Field(default_factory=list, description="Validation failure messages")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings or recommendations")


class ToolExecutionResult(BaseModel):
    """Standardized output envelope returned by an analytical tool."""

    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskExecutionResult(BaseModel):
    """Status and output of an executed task."""

    task_id: str
    status: str = Field(..., description="Task lifecycle status: completed, failed, blocked, skipped")
    attempts: int = 1
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    recovery_attempts: List[Dict[str, Any]] = Field(default_factory=list)


class ExecutionSummary(BaseModel):
    """Comprehensive summary of an investigation plan execution."""

    plan_id: str
    investigation_id: Optional[str] = None
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    blocked_tasks: int
    task_results: Dict[str, TaskExecutionResult] = Field(default_factory=dict)
    generated_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    start_time: datetime
    end_time: datetime
    duration_ms: float


# API Request/Response Models
class PlanPreviewRequest(BaseModel):
    """Request payload to preview an investigation plan."""

    business_question: str = Field(..., min_length=1, max_length=5000)
    columns: Optional[List[str]] = Field(default=None, description="Available dataset column names")
    dataset_profile: Optional[DatasetProfile] = Field(default=None, description="Optional full dataset profile")
    data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional inline data rows to infer profile from")


class PlanValidationRequest(BaseModel):
    """Request payload to validate an investigation plan."""

    plan: InvestigationPlan
    available_columns: Optional[List[str]] = Field(default=None, description="Columns available in dataset")


class ExecutionRequest(BaseModel):
    """Request payload to execute an investigation plan."""

    data: List[Dict[str, Any]] = Field(..., description="Dataset records to analyze")
    dataset_name: Optional[str] = Field(default="dataset", description="Optional dataset identifier")
