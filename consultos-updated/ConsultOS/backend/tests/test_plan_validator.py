from app.engine.validator import PlanValidator
from app.engine.schemas import InvestigationPlan, PlannedHypothesis, PlannedTask


def test_validator_valid_plan():
    """Test valid plan passes validation without errors."""
    validator = PlanValidator()
    plan = InvestigationPlan(
        plan_id="p1",
        business_question="Analyze revenue",
        hypotheses=[
            PlannedHypothesis(id="h1", statement="Stmt 1", rationale="Rat 1")
        ],
        tasks=[
            PlannedTask(
                id="t1",
                title="Profile data",
                tool_name="dataset_profiler",
                parameters={"columns": ["revenue"]},
                hypothesis_id="h1",
            ),
            PlannedTask(
                id="t2",
                title="Validate data",
                tool_name="data_validator",
                parameters={"columns": ["revenue"]},
                dependency_ids=["t1"],
                hypothesis_id="h1",
            ),
        ],
    )
    result = validator.validate(plan, available_columns=["revenue"])
    assert result.is_valid is True
    assert result.errors == []


def test_validator_duplicate_task_and_hyp_ids():
    """Test duplicate IDs are rejected."""
    validator = PlanValidator()
    plan = InvestigationPlan(
        plan_id="p2",
        business_question="Test",
        hypotheses=[
            PlannedHypothesis(id="h1", statement="S1", rationale="R1"),
            PlannedHypothesis(id="h1", statement="S2", rationale="R2"),
        ],
        tasks=[
            PlannedTask(id="t1", title="Task A", tool_name="dataset_profiler"),
            PlannedTask(id="t1", title="Task B", tool_name="dataset_profiler"),
        ],
    )
    result = validator.validate(plan)
    assert result.is_valid is False
    assert any("Duplicate task IDs" in err for err in result.errors)
    assert any("Duplicate hypothesis IDs" in err for err in result.errors)


def test_validator_unregistered_tool():
    """Test task referencing unregistered tool is rejected."""
    validator = PlanValidator()
    plan = InvestigationPlan(
        plan_id="p3",
        business_question="Test",
        tasks=[
            PlannedTask(id="t1", title="Task 1", tool_name="unapproved_arbitrary_shell_tool"),
        ],
    )
    result = validator.validate(plan)
    assert result.is_valid is False
    assert any("unregistered tool" in err for err in result.errors)


def test_validator_invalid_tool_parameters():
    """Test parameter validation detects missing required parameters or missing columns."""
    validator = PlanValidator()
    plan = InvestigationPlan(
        plan_id="p4",
        business_question="Test",
        tasks=[
            PlannedTask(
                id="t1",
                title="Time series without date col",
                tool_name="timeseries_analyzer",
                parameters={"metric_column": "sales"},  # Missing date_column!
            ),
        ],
    )
    result = validator.validate(plan, available_columns=["sales"])
    assert result.is_valid is False
    assert any("date_column' is required" in err for err in result.errors)


def test_validator_invalid_dependency_and_self_dependency():
    """Test non-existent dependency and self-dependency are rejected."""
    validator = PlanValidator()
    plan = InvestigationPlan(
        plan_id="p5",
        business_question="Test",
        tasks=[
            PlannedTask(
                id="t1",
                title="Task 1",
                tool_name="dataset_profiler",
                dependency_ids=["non_existent_task", "t1"],  # Self dependency + unknown dependency!
            ),
        ],
    )
    result = validator.validate(plan)
    assert result.is_valid is False
    assert any("depends on non-existent task" in err for err in result.errors)
    assert any("cannot depend on itself" in err for err in result.errors)


def test_validator_dependency_cycle_rejection():
    """Test circular dependencies among tasks are detected and rejected."""
    validator = PlanValidator()
    plan = InvestigationPlan(
        plan_id="p6",
        business_question="Test",
        tasks=[
            PlannedTask(
                id="t1",
                title="Task 1",
                tool_name="dataset_profiler",
                dependency_ids=["t3"],
            ),
            PlannedTask(
                id="t2",
                title="Task 2",
                tool_name="dataset_profiler",
                dependency_ids=["t1"],
            ),
            PlannedTask(
                id="t3",
                title="Task 3",
                tool_name="dataset_profiler",
                dependency_ids=["t2"],
            ),
        ],
    )
    result = validator.validate(plan)
    assert result.is_valid is False
    assert any("Circular dependency detected" in err for err in result.errors)


def test_validator_task_limits_rejection():
    """Test plan with zero tasks or more than 50 tasks is rejected."""
    validator = PlanValidator()
    # 0 tasks
    empty_plan = InvestigationPlan(plan_id="p0", business_question="Test", tasks=[])
    res_empty = validator.validate(empty_plan)
    assert res_empty.is_valid is False
    assert any("at least one task" in err for err in res_empty.errors)

    # 51 tasks
    too_many_tasks = [
        PlannedTask(id=f"t{i}", title=f"Task {i}", tool_name="dataset_profiler")
        for i in range(51)
    ]
    overflow_plan = InvestigationPlan(plan_id="p_over", business_question="Test", tasks=too_many_tasks)
    res_over = validator.validate(overflow_plan)
    assert res_over.is_valid is False
    assert any("exceeds maximum limit" in err for err in res_over.errors)
