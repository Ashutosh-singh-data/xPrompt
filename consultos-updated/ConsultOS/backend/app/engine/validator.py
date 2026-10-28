from typing import List, Optional, Set
from app.engine.schemas import InvestigationPlan, PlanValidationResult
from app.engine.tools.registry import tool_registry, ToolRegistry
from app.engine.graph import DependencyGraph

MAX_PLAN_TASKS = 50


class PlanValidator:
    """Validates structural, relational, and parameter integrity of investigation plans."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or tool_registry

    def validate(
        self,
        plan: InvestigationPlan,
        available_columns: Optional[List[str]] = None,
    ) -> PlanValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Task limits
        if not plan.tasks:
            errors.append("Plan must contain at least one task.")
        elif len(plan.tasks) > MAX_PLAN_TASKS:
            errors.append(f"Plan exceeds maximum limit of {MAX_PLAN_TASKS} tasks (found {len(plan.tasks)}).")

        # 2. Unique task and hypothesis IDs
        seen_task_ids: Set[str] = set()
        duplicate_task_ids: Set[str] = set()
        for task in plan.tasks:
            if task.id in seen_task_ids:
                duplicate_task_ids.add(task.id)
            seen_task_ids.add(task.id)

        if duplicate_task_ids:
            errors.append(f"Duplicate task IDs found: {sorted(duplicate_task_ids)}")

        seen_hyp_ids: Set[str] = set()
        duplicate_hyp_ids: Set[str] = set()
        for hyp in plan.hypotheses:
            if hyp.id in seen_hyp_ids:
                duplicate_hyp_ids.add(hyp.id)
            seen_hyp_ids.add(hyp.id)

        if duplicate_hyp_ids:
            errors.append(f"Duplicate hypothesis IDs found: {sorted(duplicate_hyp_ids)}")

        # 3. Tool registry and parameters check
        for task in plan.tasks:
            if not self.registry.has(task.tool_name):
                errors.append(
                    f"Task '{task.id}' references unregistered tool '{task.tool_name}'."
                )
            else:
                tool = self.registry.get(task.tool_name)
                if tool:
                    param_errors = tool.validate_parameters(
                        task.parameters,
                        available_columns=available_columns,
                    )
                    for err in param_errors:
                        errors.append(f"Task '{task.id}' parameter error: {err}")

        # 4. Dependency references & self-dependency checks
        graph = DependencyGraph()
        for task in plan.tasks:
            for dep_id in task.dependency_ids:
                if dep_id not in seen_task_ids:
                    errors.append(
                        f"Task '{task.id}' depends on non-existent task '{dep_id}'."
                    )
                if dep_id == task.id:
                    errors.append(f"Task '{task.id}' cannot depend on itself.")

            # Register in graph for cycle check
            valid_deps = [d for d in task.dependency_ids if d in seen_task_ids and d != task.id]
            graph.add_task(task.id, valid_deps)

        # 5. Hypothesis references
        for task in plan.tasks:
            if task.hypothesis_id and task.hypothesis_id not in seen_hyp_ids:
                errors.append(
                    f"Task '{task.id}' references non-existent hypothesis '{task.hypothesis_id}'."
                )

        # 6. Dependency cycle detection
        cycle = graph.find_cycle()
        if cycle:
            errors.append(f"Circular dependency detected among tasks: {' -> '.join(cycle)}")

        return PlanValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


plan_validator = PlanValidator()
