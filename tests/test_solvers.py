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


def test_distinct_alternatives_generation(tmp_path: pathlib.Path) -> None:
    """Verifies AssignmentEngine produces distinct alternatives."""
    create_app({"TESTING": True, "DATABASE_PATH": tmp_path / "solvers.db"})
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


def test_rank_gaps_are_read_as_positions(tmp_path: pathlib.Path) -> None:
    """Ranks with gaps (e.g. after a project is deleted) count by position (D16)."""
    create_app({"TESTING": True, "DATABASE_PATH": tmp_path / "gaps.db"})
    projects = [
        models.Project(id="P1", title="P1", min_capacity=0, max_capacity=1),
        models.Project(id="P2", title="P2", min_capacity=0, max_capacity=1),
    ]
    # S1 ranked four projects; two were deleted, leaving ranks 3 and 5
    s1 = models.Student(
        id="S1",
        display_name="S1",
        preferences=[
            models.Preference("S1", "P1", 3),
            models.Preference("S1", "P2", 5),
        ],
    )
    s2 = models.Student(
        id="S2",
        display_name="S2",
        preferences=[models.Preference("S2", "P1", 1)],
    )
    engine = solvers.AssignmentEngine()
    run = engine.run_assignment(
        [s1, s2],
        projects,
        fixed_assignments=[models.FixedAssignment("S2", "P1")],
        max_alternatives=1,
    )
    assert run.status == "COMPLETED"
    s1_asg = run.solutions[0].get_assignment_for_student("S1")
    assert s1_asg is not None
    assert s1_asg.project_id == "P2"
    # P2 is S1's second remaining choice, not an unranked project
    assert s1_asg.preference_rank == 2
    fairness = run.solutions[0].indicators["fairness"]
    assert fairness["unranked_count"] == 0
    assert fairness["worst_rank"] == 2


def test_uncatalogued_skill_is_a_warning_not_a_crash(tmp_path: pathlib.Path) -> None:
    """A skill missing from the catalogue warns (R17) and the run still completes (D16)."""
    create_app({"TESTING": True, "DATABASE_PATH": tmp_path / "skills.db"})
    projects = [
        models.Project(
            id="P1",
            title="P1",
            min_capacity=0,
            max_capacity=2,
            requirements=[models.ProjectRequirement("P1", "rust", minimum_level=2)],
        )
    ]
    s1 = models.Student(
        id="S1",
        display_name="S1",
        skills={"quantum": 3},
        preferences=[models.Preference("S1", "P1", 1)],
    )
    engine = solvers.AssignmentEngine()
    run = engine.run_assignment(
        [s1], projects, skills=[models.Skill(id="py", name="Python")], max_alternatives=1
    )
    assert run.status == "COMPLETED"
    assert any("rust" in w for w in run.diagnostics["warnings"])
    assert any("quantum" in w for w in run.diagnostics["warnings"])


def test_catalogue_names_are_not_overwritten(tmp_path: pathlib.Path) -> None:
    """Storing an uncatalogued skill never replaces an existing skill's name (D16)."""
    from app.persistence import repositories

    create_app({"TESTING": True, "DATABASE_PATH": tmp_path / "names.db"})
    repositories.SkillRepository().save(models.Skill(id="py", name="Python"))
    s1 = models.Student(
        id="S1",
        display_name="S1",
        skills={"py": 3},
        preferences=[models.Preference("S1", "P1", 1)],
    )
    projects = [models.Project(id="P1", title="P1", min_capacity=0, max_capacity=1)]
    run = solvers.AssignmentEngine().run_assignment([s1], projects, max_alternatives=1)
    assert run.status == "COMPLETED"
    stored = repositories.SkillRepository().get_by_id("py")
    assert stored is not None
    assert stored.name == "Python"


def test_invalid_input_is_reported_before_infeasibility(tmp_path: pathlib.Path) -> None:
    """Input that is both broken and infeasible is INVALID_INPUT (D16)."""
    create_app({"TESTING": True, "DATABASE_PATH": tmp_path / "invalid.db"})
    s1 = models.Student(
        id="S1",
        display_name="S1",
        preferences=[models.Preference("S1", "P1", 1)],
    )
    run = solvers.AssignmentEngine().run_assignment([s1], [], max_alternatives=1)
    assert run.status == "INVALID_INPUT"
    assert any("Project catalog cannot be empty" in e for e in run.diagnostics["errors"])
