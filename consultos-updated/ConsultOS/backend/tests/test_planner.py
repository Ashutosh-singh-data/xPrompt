import pytest
from app.engine.planner import rule_based_planner, UnsupportedQuestionError
from app.engine.schemas import DatasetProfile


def test_planner_sales_decline_generates_hypotheses_and_tasks():
    """Test planner analyzes question and dataset columns to generate structured plan."""
    question = "Why did our sales decline last month?"
    columns = ["order_date", "sales", "region", "category", "units"]
    dtypes = {"order_date": "datetime64", "sales": "float64", "region": "object", "category": "object", "units": "int64"}

    profile = DatasetProfile(
        name="sales_transactions",
        row_count=1000,
        columns=columns,
        dtypes=dtypes,
    )

    plan = rule_based_planner.plan(
        business_question=question,
        columns=columns,
        dataset_profile=profile,
    )

    assert plan.plan_id.startswith("plan_")
    assert plan.business_question == question
    assert len(plan.hypotheses) >= 2
    assert len(plan.tasks) >= 3

    # Check task tools and dependencies
    task_tools = [t.tool_name for t in plan.tasks]
    assert "dataset_profiler" in task_tools
    assert "data_validator" in task_tools
    assert "grouped_aggregator" in task_tools or "timeseries_analyzer" in task_tools

    # Verify profiling has no dependencies and validation depends on profiling
    profiling_task = next(t for t in plan.tasks if t.tool_name == "dataset_profiler")
    assert profiling_task.dependency_ids == []

    validation_task = next(t for t in plan.tasks if t.tool_name == "data_validator")
    assert profiling_task.id in validation_task.dependency_ids


def test_planner_does_not_hallucinate_columns():
    """Test planner only uses columns that exist in the dataset."""
    question = "Why did product revenue drop?"
    columns = ["product_id", "revenue", "store_code"]

    plan = rule_based_planner.plan(
        business_question=question,
        columns=columns,
    )

    for task in plan.tasks:
        params = task.parameters
        if "columns" in params:
            for c in params["columns"]:
                assert c in columns
        if "metric_column" in params:
            assert params["metric_column"] in columns
        if "group_by" in params:
            for c in params["group_by"]:
                assert c in columns


def test_planner_rejects_empty_question():
    """Test empty business question raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        rule_based_planner.plan(business_question="", columns=["a", "b"])


def test_planner_rejects_empty_columns():
    """Test dataset with no columns raises UnsupportedQuestionError."""
    with pytest.raises(UnsupportedQuestionError):
        rule_based_planner.plan(
            business_question="Analyze sales",
            columns=[],
        )


def test_planner_rejects_unsupported_question():
    """Test question asking about HR/turnover when dataset has zero HR columns."""
    question = "Why did employee turnover and attrition spike?"
    columns = ["sensor_id", "temperature", "pressure", "reading_time"]

    with pytest.raises(UnsupportedQuestionError):
        rule_based_planner.plan(
            business_question=question,
            columns=columns,
        )
