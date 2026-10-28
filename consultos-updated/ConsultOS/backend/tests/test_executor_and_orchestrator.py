import pandas as pd
from app.engine.executor import TaskExecutor
from app.engine.orchestrator import InvestigationOrchestrator
from app.engine.schemas import InvestigationPlan, PlannedTask, PlannedHypothesis


def test_orchestrator_multi_task_execution():
    """Test orchestrator executes multi-task plan sequentially in dependency order."""
    orchestrator = InvestigationOrchestrator()
    df = pd.DataFrame({
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "sales": [100.0, 200.0, 300.0],
        "category": ["A", "B", "A"],
    })

    plan = InvestigationPlan(
        plan_id="plan_orch_1",
        business_question="Test orchestrator",
        tasks=[
            PlannedTask(
                id="t1",
                title="Profile dataset",
                tool_name="dataset_profiler",
                parameters={"columns": ["sales", "category"]},
                dependency_ids=[],
            ),
            PlannedTask(
                id="t2",
                title="Validate dataset",
                tool_name="data_validator",
                parameters={"columns": ["sales", "category"]},
                dependency_ids=["t1"],
            ),
            PlannedTask(
                id="t3",
                title="Aggregate sales by category",
                tool_name="grouped_aggregator",
                parameters={
                    "group_by": ["category"],
                    "aggregations": {"sales": ["sum"]},
                },
                dependency_ids=["t2"],
            ),
        ],
    )

    summary = orchestrator.run(plan, df)
    assert summary.total_tasks == 3
    assert summary.completed_tasks == 3
    assert summary.failed_tasks == 0
    assert summary.blocked_tasks == 0
    assert summary.task_results["t1"].status == "completed"
    assert summary.task_results["t2"].status == "completed"
    assert summary.task_results["t3"].status == "completed"
    assert len(summary.generated_evidence) >= 1


def test_orchestrator_dependency_blocking_and_independent_continuation():
    """Test when one branch fails, downstream tasks are blocked while independent branches continue."""
    orchestrator = InvestigationOrchestrator()
    # order_date has invalid date strings so timeseries_analyzer will fail at runtime
    df = pd.DataFrame({
        "order_date": ["not_a_date_1", "not_a_date_2", "not_a_date_3"],
        "sales": [10.0, 20.0, 30.0],
        "region": ["East", "West", "East"],
    })

    # Plan structure:
    # Branch 1: t_fail (fails at runtime because date cannot be parsed) -> t_blocked (depends on t_fail)
    # Branch 2 (Independent): t_indep1 (valid) -> t_indep2 (depends on t_indep1)
    plan = InvestigationPlan(
        plan_id="plan_branch_test",
        business_question="Test branching",
        tasks=[
            PlannedTask(
                id="t_fail",
                title="Task designed to fail at runtime",
                tool_name="timeseries_analyzer",
                parameters={"date_column": "order_date", "metric_column": "sales"},
                dependency_ids=[],
            ),
            PlannedTask(
                id="t_blocked",
                title="Task depending on failed task",
                tool_name="dataset_profiler",
                parameters={"columns": ["sales"]},
                dependency_ids=["t_fail"],
            ),
            PlannedTask(
                id="t_indep1",
                title="Independent task 1",
                tool_name="dataset_profiler",
                parameters={"columns": ["sales"]},
                dependency_ids=[],
            ),
            PlannedTask(
                id="t_indep2",
                title="Independent task 2",
                tool_name="grouped_aggregator",
                parameters={
                    "group_by": ["region"],
                    "aggregations": {"sales": ["sum"]},
                },
                dependency_ids=["t_indep1"],
            ),
        ],
    )

    summary = orchestrator.run(plan, df)
    assert summary.total_tasks == 4
    # Independent branch succeeded
    assert summary.task_results["t_indep1"].status == "completed"
    assert summary.task_results["t_indep2"].status == "completed"
    assert summary.completed_tasks == 2

    # Failed task is failed, NOT completed
    assert summary.task_results["t_fail"].status == "failed"
    assert summary.failed_tasks == 1

    # Downstream task is blocked
    assert summary.task_results["t_blocked"].status == "blocked"
    assert summary.blocked_tasks == 1


def test_failed_tasks_never_marked_completed():
    """Verify task executor strictly enforces failure status."""
    executor = TaskExecutor()
    df = pd.DataFrame({"col": [1, 2, 3]})

    # Unregistered tool
    task_bad_tool = PlannedTask(
        id="t_bad",
        title="Bad",
        tool_name="non_existent_tool_xyz",
    )
    res = executor.execute_task(task_bad_tool, df, {})
    assert res.status == "failed"
    assert res.result is None
    assert "Unregistered" in res.error
