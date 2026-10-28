import pytest
import pandas as pd
from app.engine.schemas import InvestigationPlan, PlannedTask, PlannedHypothesis, TaskExecutionResult
from app.engine.replanner import DynamicReplanner
from app.models.hypothesis import Hypothesis, HypothesisStatus
from app.models.evidence import Evidence, EvidenceVerificationStatus


def test_replanning_triggered_on_task_failure():
    """Ensure replanner generates compensatory follow-up task when a task fails."""
    replanner = DynamicReplanner(max_replan_iterations=2, max_total_tasks=10)

    plan = InvestigationPlan(
        plan_id="p1",
        business_question="Why did product sales drop?",
        tasks=[
            PlannedTask(
                id="task_1",
                title="Profile data",
                tool_name="dataset_profiler",
                parameters={},
                dependency_ids=[],
            ),
            PlannedTask(
                id="task_2",
                title="Time-series analysis",
                tool_name="timeseries_analyzer",
                parameters={"date_column": "order_date", "metric_column": "sales", "frequency": "ME"},
                dependency_ids=["task_1"],
            ),
        ],
    )

    df = pd.DataFrame([
        {"order_date": "2026-01-01", "sales": 100, "region": "North"},
        {"order_date": "2026-02-01", "sales": 150, "region": "South"},
    ])

    completed_results = {
        "task_1": TaskExecutionResult(task_id="task_1", status="completed", attempts=1, result={"row_count": 2}),
        "task_2": TaskExecutionResult(task_id="task_2", status="failed", attempts=2, error="Invalid date format"),
    }

    replan_eval = replanner.evaluate_and_replan(
        plan=plan,
        completed_results=completed_results,
        evidence_list=[],
        hypotheses=[],
        df=df,
        current_replan_iteration=0,
    )

    assert replan_eval.needed is True
    assert replan_eval.trigger == "task_failure"
    assert "failed" in replan_eval.unresolved_question.lower()
    assert len(replan_eval.follow_up_tasks) >= 1
    # Check that follow-up task uses approved tool and depends on successful task_1
    follow_up = replan_eval.follow_up_tasks[0]
    assert follow_up.tool_name in ["grouped_aggregator", "dataset_profiler", "data_validator"]
    assert "task_1" in follow_up.dependency_ids


def test_replanning_prevents_duplicate_tasks():
    """Ensure replanner does not generate tasks identical to already existing tasks."""
    replanner = DynamicReplanner(max_replan_iterations=2, max_total_tasks=10)

    # Initial plan already has the grouped aggregator task for region and sales
    existing_task = PlannedTask(
        id="task_existing",
        title="Analyze sales by region",
        tool_name="grouped_aggregator",
        parameters={"group_by": ["region"], "metric_column": "sales", "agg_funcs": ["sum", "mean", "count"]},
        dependency_ids=[],
    )

    plan = InvestigationPlan(
        plan_id="p2",
        business_question="Analyze sales",
        tasks=[existing_task],
    )

    df = pd.DataFrame([{"sales": 500, "region": "North"}])

    # Inconclusive hypothesis on dimensional concentration
    hyp = Hypothesis(
        id="h_inc",
        investigation_id="inv1",
        statement="The shift in sales is concentrated within specific segments of region rather than uniform.",
        status=HypothesisStatus.INCONCLUSIVE.value,
    )

    replan_eval = replanner.evaluate_and_replan(
        plan=plan,
        completed_results={"task_existing": TaskExecutionResult(task_id="task_existing", status="completed")},
        evidence_list=[],
        hypotheses=[hyp],
        df=df,
        current_replan_iteration=0,
    )

    # Should NOT generate a duplicate grouped_aggregator for region and sales!
    for t in replan_eval.follow_up_tasks:
        assert not (t.tool_name == "grouped_aggregator" and t.parameters.get("group_by") == ["region"])


def test_replanning_enforces_iteration_and_total_task_limits():
    """Ensure replanning stops when max iterations or max total tasks are reached."""
    replanner = DynamicReplanner(max_replan_iterations=2, max_total_tasks=3)

    plan = InvestigationPlan(
        plan_id="p3",
        business_question="Test limits",
        tasks=[
            PlannedTask(id="t1", title="Task 1", tool_name="dataset_profiler", parameters={}),
            PlannedTask(id="t2", title="Task 2", tool_name="data_validator", parameters={}),
            PlannedTask(id="t3", title="Task 3", tool_name="grouped_aggregator", parameters={"metric_column": "v"}),
        ],
    )

    df = pd.DataFrame([{"v": 10}])

    # 1. Test task count cap reached (already 3 tasks, max is 3)
    eval_task_cap = replanner.evaluate_and_replan(
        plan=plan,
        completed_results={"t1": TaskExecutionResult(task_id="t1", status="failed")},
        evidence_list=[],
        hypotheses=[],
        df=df,
        current_replan_iteration=0,
    )
    assert eval_task_cap.needed is False
    assert eval_task_cap.trigger == "limit_reached"

    # 2. Test iteration cap reached (current_replan_iteration=2, max is 2)
    plan_small = InvestigationPlan(
        plan_id="p4",
        business_question="Test small",
        tasks=[PlannedTask(id="t1", title="Task 1", tool_name="dataset_profiler", parameters={})],
    )
    eval_iter_cap = replanner.evaluate_and_replan(
        plan=plan_small,
        completed_results={"t1": TaskExecutionResult(task_id="t1", status="failed")},
        evidence_list=[],
        hypotheses=[],
        df=df,
        current_replan_iteration=2,
    )
    assert eval_iter_cap.needed is False
    assert eval_iter_cap.trigger == "limit_reached"


def test_replanning_triggered_on_data_quality_issue():
    """Ensure data quality issue triggers follow-up distribution assessment task."""
    replanner = DynamicReplanner()

    plan = InvestigationPlan(
        plan_id="p5",
        business_question="Check revenue anomaly",
        tasks=[
            PlannedTask(
                id="task_val",
                title="Data validation",
                tool_name="data_validator",
                parameters={},
            ),
        ],
    )

    df = pd.DataFrame([
        {"revenue": -50.0, "client": "A"},
        {"revenue": 100.0, "client": "B"},
    ])

    completed_results = {
        "task_val": TaskExecutionResult(
            task_id="task_val",
            status="completed",
            result={"is_valid": False, "issues": [{"type": "negative_values", "severity": "high"}]},
        ),
    }

    replan_eval = replanner.evaluate_and_replan(
        plan=plan,
        completed_results=completed_results,
        evidence_list=[],
        hypotheses=[],
        df=df,
        current_replan_iteration=0,
    )

    assert replan_eval.needed is True
    assert replan_eval.trigger == "data_quality_issue"
    assert any(t.tool_name == "grouped_aggregator" for t in replan_eval.follow_up_tasks)
