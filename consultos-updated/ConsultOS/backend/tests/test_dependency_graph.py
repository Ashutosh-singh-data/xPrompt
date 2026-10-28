import pytest
from app.engine.graph import DependencyGraph, DependencyCycleError


def test_graph_topological_sort_deterministic():
    """Test topological sort returns deterministic dependency order."""
    graph = DependencyGraph()
    # t3 depends on t1, t2 depends on t1, t4 depends on t2 and t3
    graph.add_task("t1", [])
    graph.add_task("t2", ["t1"])
    graph.add_task("t3", ["t1"])
    graph.add_task("t4", ["t2", "t3"])

    order = graph.topological_sort()
    assert order[0] == "t1"
    assert order.index("t1") < order.index("t2")
    assert order.index("t1") < order.index("t3")
    assert order.index("t2") < order.index("t4")
    assert order.index("t3") < order.index("t4")


def test_graph_cycle_detection():
    """Test circular dependency raises DependencyCycleError."""
    graph = DependencyGraph()
    graph.add_task("A", ["B"])
    graph.add_task("B", ["C"])
    graph.add_task("C", ["A"])

    assert graph.has_cycle() is True
    cycle = graph.find_cycle()
    assert cycle is not None
    assert len(cycle) >= 3

    with pytest.raises(DependencyCycleError):
        graph.topological_sort()


def test_graph_ready_tasks_progression():
    """Test get_ready_tasks accurately reflects completed prerequisites."""
    graph = DependencyGraph()
    graph.add_task("t1", [])
    graph.add_task("t2", ["t1"])
    graph.add_task("t3", ["t1"])
    graph.add_task("t4", ["t2", "t3"])

    # Initially only t1 has no prereqs
    ready_0 = graph.get_ready_tasks(completed_task_ids=set(), processed_or_active_ids=set())
    assert ready_0 == ["t1"]

    # When t1 completes, t2 and t3 become ready
    ready_1 = graph.get_ready_tasks(
        completed_task_ids={"t1"},
        processed_or_active_ids={"t1"},
    )
    assert sorted(ready_1) == ["t2", "t3"]

    # When t2 completes, t4 is still not ready because t3 is not complete
    ready_2 = graph.get_ready_tasks(
        completed_task_ids={"t1", "t2"},
        processed_or_active_ids={"t1", "t2"},
    )
    assert ready_2 == ["t3"]

    # When both t2 and t3 complete, t4 becomes ready
    ready_3 = graph.get_ready_tasks(
        completed_task_ids={"t1", "t2", "t3"},
        processed_or_active_ids={"t1", "t2", "t3"},
    )
    assert ready_3 == ["t4"]


def test_graph_blocked_tasks_on_failure():
    """Test get_blocked_tasks identifies direct and transitive downstream dependents."""
    graph = DependencyGraph()
    # A -> B -> C -> D
    # Independent branch: X -> Y
    graph.add_task("A", [])
    graph.add_task("B", ["A"])
    graph.add_task("C", ["B"])
    graph.add_task("D", ["C"])

    graph.add_task("X", [])
    graph.add_task("Y", ["X"])

    # If B fails, C and D are blocked, but X and Y are unaffected!
    blocked = graph.get_blocked_tasks(failed_task_ids={"B"})
    assert blocked == {"C", "D"}
    assert "X" not in blocked
    assert "Y" not in blocked
