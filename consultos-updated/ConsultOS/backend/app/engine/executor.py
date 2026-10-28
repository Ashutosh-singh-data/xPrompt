import time
import logging
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from app.engine.schemas import PlannedTask, TaskExecutionResult
from app.engine.tools.registry import tool_registry, ToolRegistry

logger = logging.getLogger("consultos.engine.executor")

NON_RETRYABLE_ERROR_SUBSTRINGS = [
    "Unregistered analytical tool",
    "Parameter validation failed",
    "Columns not found in dataset",
    "Non-negative columns not found",
    "must be a list",
    "Unsupported aggregation function",
]


def is_retryable_error(error_message: str, exc: Optional[Exception] = None) -> bool:
    """Classify an analytical execution failure as retryable vs non-retryable."""
    if any(non_ret in error_message for non_ret in NON_RETRYABLE_ERROR_SUBSTRINGS):
        return False
    if exc is not None and isinstance(exc, (ValueError, KeyError, TypeError)):
        if "not found in dataset" in str(exc) or "cannot depend" in str(exc):
            return False
    return True


class TaskExecutor:
    """Executes planned analytical tasks using registered tools with bounded failure recovery."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or tool_registry

    def execute_task(
        self,
        task: PlannedTask,
        df: pd.DataFrame,
        completed_results: Dict[str, TaskExecutionResult],
        max_retries: Optional[int] = None,
        base_backoff_sec: float = 0.02,
        on_retry: Optional[Callable[[str, int, str], None]] = None,
    ) -> TaskExecutionResult:
        """Execute a single task against the dataset with dependency checks and bounded failure recovery."""
        start_time = time.perf_counter()

        # 1. Dependency check
        for dep_id in task.dependency_ids:
            dep_res = completed_results.get(dep_id)
            if not dep_res or dep_res.status != "completed":
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.warning(
                    f"Task '{task.id}' cannot run: dependency '{dep_id}' is not completed."
                )
                return TaskExecutionResult(
                    task_id=task.id,
                    status="blocked",
                    attempts=0,
                    error=f"Prerequisite task '{dep_id}' did not complete successfully.",
                    execution_time_ms=round(duration_ms, 2),
                )

        # 2. Tool resolution
        tool = self.registry.get(task.tool_name)
        if not tool:
            duration_ms = (time.perf_counter() - start_time) * 1000
            err_msg = f"Unregistered analytical tool: '{task.tool_name}'."
            logger.error(f"Task '{task.id}' references unknown tool '{task.tool_name}'.")
            return TaskExecutionResult(
                task_id=task.id,
                status="failed",
                attempts=1,
                error=err_msg,
                execution_time_ms=round(duration_ms, 2),
                recovery_attempts=[{
                    "attempt": 1,
                    "error": err_msg,
                    "retryable": False,
                }],
            )

        # 3. Parameter validation
        param_errors = tool.validate_parameters(
            task.parameters,
            available_columns=list(df.columns),
        )
        if param_errors:
            duration_ms = (time.perf_counter() - start_time) * 1000
            err_msg = f"Parameter validation failed: {'; '.join(param_errors)}"
            logger.error(f"Task '{task.id}' parameter validation failed: {param_errors}")
            return TaskExecutionResult(
                task_id=task.id,
                status="failed",
                attempts=1,
                error=err_msg,
                execution_time_ms=round(duration_ms, 2),
                recovery_attempts=[{
                    "attempt": 1,
                    "error": err_msg,
                    "retryable": False,
                }],
            )

        # 4. Bounded execution with retry loop
        effective_retries = (
            max_retries if max_retries is not None else task.parameters.get("max_retries", 2)
        )
        max_attempts = 1 + max(0, effective_retries)
        recovery_attempts: List[Dict[str, Any]] = []

        for attempt in range(1, max_attempts + 1):
            try:
                tool_output = tool.execute(df, task.parameters)
                duration_ms = (time.perf_counter() - start_time) * 1000

                if tool_output.success:
                    logger.info(
                        f"Task '{task.id}' completed successfully on attempt {attempt} in {duration_ms:.2f}ms."
                    )
                    return TaskExecutionResult(
                        task_id=task.id,
                        status="completed",
                        attempts=attempt,
                        result=tool_output.data,
                        execution_time_ms=round(duration_ms, 2),
                        recovery_attempts=recovery_attempts,
                    )

                # Tool returned unsuccessful result
                err = tool_output.error or "Tool returned failure status."
                retryable = is_retryable_error(err)
                recovery_attempts.append({
                    "attempt": attempt,
                    "error": err,
                    "retryable": retryable,
                })
                logger.warning(
                    f"Task '{task.id}' attempt {attempt}/{max_attempts} failed: {err} (retryable={retryable})"
                )

                if retryable and attempt < max_attempts:
                    if on_retry:
                        on_retry(task.id, attempt, err)
                    backoff = base_backoff_sec * (2 ** (attempt - 1))
                    time.sleep(backoff)
                    continue

                return TaskExecutionResult(
                    task_id=task.id,
                    status="failed",
                    attempts=attempt,
                    error=err,
                    execution_time_ms=round(duration_ms, 2),
                    recovery_attempts=recovery_attempts,
                )

            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                err = f"Execution exception: {str(exc)}"
                retryable = is_retryable_error(err, exc)
                recovery_attempts.append({
                    "attempt": attempt,
                    "error": err,
                    "retryable": retryable,
                })
                logger.error(
                    f"Task '{task.id}' attempt {attempt}/{max_attempts} raised exception: {exc} (retryable={retryable})",
                    exc_info=True,
                )

                if retryable and attempt < max_attempts:
                    if on_retry:
                        on_retry(task.id, attempt, err)
                    backoff = base_backoff_sec * (2 ** (attempt - 1))
                    time.sleep(backoff)
                    continue

                return TaskExecutionResult(
                    task_id=task.id,
                    status="failed",
                    attempts=attempt,
                    error=err,
                    execution_time_ms=round(duration_ms, 2),
                    recovery_attempts=recovery_attempts,
                )

        # Fallback if loop finishes unexpectedly
        duration_ms = (time.perf_counter() - start_time) * 1000
        return TaskExecutionResult(
            task_id=task.id,
            status="failed",
            attempts=max_attempts,
            error="Task exceeded retry limits without completing.",
            execution_time_ms=round(duration_ms, 2),
            recovery_attempts=recovery_attempts,
        )


task_executor = TaskExecutor()

