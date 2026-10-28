import pytest
import pandas as pd
from typing import Dict, Any, List
from app.engine.schemas import PlannedTask, TaskExecutionResult
from app.engine.executor import TaskExecutor, is_retryable_error
from app.engine.tools.base import BaseTool
from app.engine.tools.registry import ToolRegistry


class TransientFailingTool(BaseTool):
    """Mock tool that fails a configurable number of times before succeeding."""

    name = "transient_tool"
    description = "Fails intermittently for testing retry recovery."

    def __init__(self, failures_before_success: int = 1):
        self.failures_before_success = failures_before_success
        self.call_count = 0

    def validate_parameters(self, parameters: Dict[str, Any], available_columns=None) -> List[str]:
        return []

    def execute(self, df: pd.DataFrame, parameters: Dict[str, Any]):
        self.call_count += 1
        if self.call_count <= self.failures_before_success:
            return type("Result", (), {
                "success": False,
                "data": None,
                "error": "Transient database timeout encountered during calculation.",
            })()
        return type("Result", (), {
            "success": True,
            "data": {"processed_rows": len(df)},
            "error": None,
        })()


class PermanentFailingTool(BaseTool):
    """Mock tool that fails permanently."""

    name = "permanent_tool"
    description = "Fails permanently."

    def __init__(self):
        self.call_count = 0

    def validate_parameters(self, parameters: Dict[str, Any], available_columns=None) -> List[str]:
        return []

    def execute(self, df: pd.DataFrame, parameters: Dict[str, Any]):
        self.call_count += 1
        return type("Result", (), {
            "success": False,
            "data": None,
            "error": "Non-recoverable syntax error in analytical query.",
        })()


def test_retryable_vs_non_retryable_error_classification():
    """Ensure non-retryable errors (e.g. parameter errors, missing columns) are identified."""
    assert is_retryable_error("Transient database timeout") is True
    assert is_retryable_error("Unregistered analytical tool: 'unknown_tool'") is False
    assert is_retryable_error("Parameter validation failed: missing columns") is False
    assert is_retryable_error("Columns not found in dataset: ['xyz']") is False


def test_bounded_recovery_succeeds_on_transient_error():
    """Test that transient failure recovers within configured retry limit."""
    mock_registry = ToolRegistry()
    transient_tool = TransientFailingTool(failures_before_success=1)
    mock_registry.register(transient_tool)

    executor = TaskExecutor(registry=mock_registry)
    task = PlannedTask(
        id="t1",
        title="Transient Test",
        tool_name="transient_tool",
        parameters={},
    )
    df = pd.DataFrame([{"a": 1}, {"a": 2}])

    retried_tasks = []

    def on_retry(tid, att, err):
        retried_tasks.append((tid, att, err))

    result = executor.execute_task(
        task=task,
        df=df,
        completed_results={},
        max_retries=2,
        base_backoff_sec=0.005,
        on_retry=on_retry,
    )

    assert result.status == "completed"
    assert result.attempts == 2
    assert len(result.recovery_attempts) == 1
    assert len(retried_tasks) == 1
    assert result.result == {"processed_rows": 2}


def test_non_retryable_parameter_error_aborts_immediately():
    """Ensure parameter validation failure does not retry repeatedly."""
    executor = TaskExecutor()
    task = PlannedTask(
        id="t_bad_params",
        title="Bad Params Task",
        tool_name="grouped_aggregator",
        # Missing required parameter metric_column or aggregations
        parameters={"group_by": ["non_existent_dim"]},
    )
    df = pd.DataFrame([{"sales": 100}])

    result = executor.execute_task(
        task=task,
        df=df,
        completed_results={},
        max_retries=3,
        base_backoff_sec=0.005,
    )

    assert result.status == "failed"
    # Never retries parameter validation errors! Attempts must be 1.
    assert result.attempts == 1
    assert "Parameter validation failed" in result.error
    assert len(result.recovery_attempts) == 1
    assert result.recovery_attempts[0]["retryable"] is False


def test_permanent_failure_enforces_retry_limits():
    """Ensure permanent failure exhausts retries and stops at max_attempts without marking completed."""
    mock_registry = ToolRegistry()
    perm_tool = PermanentFailingTool()
    mock_registry.register(perm_tool)

    executor = TaskExecutor(registry=mock_registry)
    task = PlannedTask(
        id="t_perm",
        title="Permanent Fail Task",
        tool_name="permanent_tool",
        parameters={},
    )
    df = pd.DataFrame([{"x": 1}])

    result = executor.execute_task(
        task=task,
        df=df,
        completed_results={},
        max_retries=2,
        base_backoff_sec=0.005,
    )

    # Must be failed, NOT completed!
    assert result.status == "failed"
    # Initial attempt + 2 retries = 3 attempts
    assert result.attempts == 3
    assert perm_tool.call_count == 3
    assert len(result.recovery_attempts) == 3


def test_dependency_blocking_and_successful_result_preservation():
    """Ensure failed prerequisite blocks dependent task while prior successful task is preserved."""
    executor = TaskExecutor()
    completed_results: Dict[str, TaskExecutionResult] = {
        "task_1": TaskExecutionResult(task_id="task_1", status="completed", attempts=1, result={"ok": True}),
        "task_2": TaskExecutionResult(task_id="task_2", status="failed", attempts=2, error="Failed"),
    }

    # Task 3 depends on Task 2 (which failed)
    task_3 = PlannedTask(
        id="task_3",
        title="Dependent Task",
        tool_name="data_validator",
        parameters={},
        dependency_ids=["task_2"],
    )

    df = pd.DataFrame([{"a": 1}])
    result_3 = executor.execute_task(
        task=task_3,
        df=df,
        completed_results=completed_results,
    )

    assert result_3.status == "blocked"
    assert result_3.attempts == 0
    assert "Prerequisite task 'task_2' did not complete successfully" in result_3.error
    # Prior successful task 1 is preserved
    assert completed_results["task_1"].status == "completed"
