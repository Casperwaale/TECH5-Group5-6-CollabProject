"""Unit tests for optimization solvers and distinct alternative generation."""

import pathlib

import pytest

from app import create_app
from app.contract import contract
from app.domain import models
from app.engine import solvers
from app.samples import demo_data


def test_assignment_strategy_abc() -> None:
    """Verifies that AssignmentStrategy cannot be instantiated directly."""
    with pytest.raises(TypeError):
        solvers.AssignmentStrategy()  # type: ignore[abstract]


def test_assignment_engine_initialization() -> None:
    """Verifies that AssignmentEngine registers the three strategies the UI sends."""
    engine = solvers.AssignmentEngine()
    assert isinstance(engine, contract.AssignmentEngineContract)
    assert isinstance(engine.strategies, dict)
    assert list(engine.strategies) == ["PREFERENCE", "SKILL_FIT", "BALANCED"]
    for key, strategy in engine.strategies.items():
        assert isinstance(strategy, solvers.AssignmentStrategy)
        assert strategy.name == key


def test_assignment_engine_raises_not_implemented(tmp_path: pathlib.Path) -> None:
    """Verifies that execute_run completes a run with indicators (R8)."""
    create_app({"TESTING": True, "DATABASE_PATH": tmp_path / "test_solvers.db"})
    engine = solvers.AssignmentEngine()
    benchmark = demo_data.get_standard_scenario()
    request = contract.RunRequest(
        students=benchmark["students"],
        projects=benchmark["projects"],
        skills=benchmark["skills"],
    )
    run = engine.execute_run(request)
    assert run.status == "COMPLETED"
    assert len(run.solutions) >= 1
    for solution in run.solutions:
        assert len(solution.assignments) == len(benchmark["students"])
        assert "mean_rank" in solution.indicators["fairness"]


def test_distinct_alternatives_generation() -> None:
    """Verifies AssignmentEngine produces distinct alternatives."""
    benchmark = demo_data.get_standard_scenario()
    engine = solvers.AssignmentEngine()

    run = engine.run_assignment(
        students=benchmark["students"],
        projects=benchmark["projects"],
        skills=benchmark["skills"],
        max_alternatives=3,
    )

    assert run.status == "COMPLETED"
    assert len(run.solutions) >= 2

    # Check distinctness: verify that each pair of solutions differs
    for i in range(len(run.solutions)):
        for j in range(i + 1, len(run.solutions)):
            pairs_i = {
                (a.student_id, a.project_id)
                for a in run.solutions[i].assignments
            }
            pairs_j = {
                (a.student_id, a.project_id)
                for a in run.solutions[j].assignments
            }
            assert (
                pairs_i != pairs_j
            ), f"Solution {i+1} and {j+1} are duplicate allocations!"
