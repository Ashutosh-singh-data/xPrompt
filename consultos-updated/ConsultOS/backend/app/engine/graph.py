from typing import Dict, Set, List, Tuple, Optional
from collections import deque


class DependencyCycleError(Exception):
    """Raised when a circular dependency is detected in the investigation plan."""

    def __init__(self, cycle: List[str]):
        super().__init__(f"Circular dependency detected among tasks: {' -> '.join(cycle)}")
        self.cycle = cycle


class DependencyGraph:
    """Directed Acyclic Graph (DAG) manager for analytical task dependencies."""

    def __init__(self):
        # task_id -> set of prerequisite task IDs it depends on
        self._prerequisites: Dict[str, Set[str]] = {}
        # task_id -> set of downstream task IDs that depend on it
        self._dependents: Dict[str, Set[str]] = {}

    def add_task(self, task_id: str, dependency_ids: Optional[List[str]] = None) -> None:
        """Register a task and its prerequisites."""
        if task_id not in self._prerequisites:
            self._prerequisites[task_id] = set()
        if task_id not in self._dependents:
            self._dependents[task_id] = set()

        deps = dependency_ids or []
        for dep in deps:
            if dep == task_id:
                raise ValueError(f"Task '{task_id}' cannot depend on itself.")
            self._prerequisites[task_id].add(dep)
            if dep not in self._dependents:
                self._dependents[dep] = set()
            self._dependents[dep].add(task_id)

    @property
    def all_task_ids(self) -> Set[str]:
        """Return all registered task IDs."""
        return set(self._prerequisites.keys())

    def get_prerequisites(self, task_id: str) -> Set[str]:
        """Return the prerequisite tasks required by task_id."""
        return self._prerequisites.get(task_id, set())

    def get_dependents(self, task_id: str) -> Set[str]:
        """Return downstream tasks depending directly on task_id."""
        return self._dependents.get(task_id, set())

    def find_cycle(self) -> Optional[List[str]]:
        """Detect if there is a cycle using DFS with 3-color marking.

        Returns:
            List of task IDs forming a cycle if found, or None.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in self._prerequisites}
        parent = {}
        cycle = []

        def dfs(node: str) -> bool:
            color[node] = GRAY
            # Prereqs point into node (prereq -> node in execution flow)
            for prereq in self._prerequisites.get(node, []):
                if prereq not in color:
                    continue  # Missing node handled by external validator
                if color[prereq] == GRAY:
                    # Found back-edge (cycle)
                    cycle.append(prereq)
                    curr = node
                    while curr != prereq:
                        cycle.append(curr)
                        curr = parent.get(curr, prereq)
                    cycle.append(prereq)
                    cycle.reverse()
                    return True
                elif color[prereq] == WHITE:
                    parent[prereq] = node
                    if dfs(prereq):
                        return True
            color[node] = BLACK
            return False

        for node in list(self._prerequisites.keys()):
            if color[node] == WHITE:
                if dfs(node):
                    return cycle
        return None

    def has_cycle(self) -> bool:
        """Return True if the dependency graph contains any cycles."""
        return self.find_cycle() is not None

    def topological_sort(self) -> List[str]:
        """Produce a deterministic topological ordering of all tasks.

        Raises:
            DependencyCycleError if a cycle is present.
        """
        cycle = self.find_cycle()
        if cycle:
            raise DependencyCycleError(cycle)

        # Kahn's Algorithm with in-degree = number of unsatisfied prerequisites
        in_degree = {node: len(self._prerequisites[node]) for node in self._prerequisites}

        # Priority queue / sorted list for deterministic ordering
        ready = [node for node, deg in in_degree.items() if deg == 0]
        ready.sort()

        order = []
        while ready:
            curr = ready.pop(0)
            order.append(curr)

            # For each task depending on curr, decrement in-degree
            for dep in sorted(self._dependents.get(curr, set())):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    ready.append(dep)
                    ready.sort()

        if len(order) != len(self._prerequisites):
            raise DependencyCycleError(["Cycle detected in unresolved dependencies."])

        return order

    def get_ready_tasks(
        self,
        completed_task_ids: Set[str],
        processed_or_active_ids: Set[str],
    ) -> List[str]:
        """Return tasks that are ready to execute:

        - All prerequisites have completed successfully
        - Not already completed, running, failed, or blocked
        """
        ready = []
        for task_id, prereqs in self._prerequisites.items():
            if task_id in processed_or_active_ids:
                continue
            if prereqs.issubset(completed_task_ids):
                ready.append(task_id)
        ready.sort()
        return ready

    def get_blocked_tasks(self, failed_task_ids: Set[str]) -> Set[str]:
        """Find all tasks that directly or transitively depend on failed tasks."""
        blocked = set()
        queue = deque(failed_task_ids)

        while queue:
            curr = queue.popleft()
            for dep in self._dependents.get(curr, set()):
                if dep not in blocked:
                    blocked.add(dep)
                    queue.append(dep)

        return blocked
