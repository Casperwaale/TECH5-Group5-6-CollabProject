"""Team A tests for the side-by-side solution comparison page."""

import pathlib
import uuid

import flask.testing

from app import create_app
from app.domain import models
from app.persistence import repositories


def _client(tmp_path: pathlib.Path) -> flask.testing.FlaskClient:
    """Creates a test client backed by a fresh database."""
    app = create_app(
        {"TESTING": True, "DATABASE_PATH": tmp_path / "compare.db"}
    )
    return app.test_client()


def _engine_run(client: flask.testing.FlaskClient) -> models.AssignmentRun:
    """Loads the standard scenario, runs it, and returns the stored run."""
    client.post("/load-scenario/standard")
    client.post(
        "/runs/trigger",
        data={"primary_strategy": "PREFERENCE", "max_alternatives": 3},
    )
    return repositories.RunRepository().list_runs(limit=1)[0]


def _seed_small_cohort() -> None:
    """Two students and two projects, with readable names."""
    proj_repo = repositories.ProjectRepository()
    for project_id, title in (("P1", "FinTech Risk"), ("P2", "Data Lakehouse")):
        proj_repo.save(
            models.Project(id=project_id, title=title, max_capacity=2)
        )
    stud_repo = repositories.StudentRepository()
    stud_repo.save(
        models.Student(
            id="S1",
            display_name="Alice Chen",
            preferences=[models.Preference("S1", "P1", 1)],
        )
    )
    stud_repo.save(
        models.Student(
            id="S2",
            display_name="Bob Berg",
            preferences=[
                models.Preference("S2", "P1", 1),
                models.Preference("S2", "P2", 2),
            ],
        )
    )


def _store_run(
    allocations: list[list[tuple[str, str, int | None]]],
) -> list[str]:
    """Stores one run with a solution per allocation list.

    Args:
        allocations: For each solution, (student, project, rank) triples.

    Returns:
        The stored solution IDs in order.
    """
    run_id = str(uuid.uuid4())
    solutions = [
        models.Solution(
            id=str(uuid.uuid4()),
            run_id=run_id,
            alternative_number=number,
            strategy_name="TEST",
            assignments=[
                models.Assignment(
                    student_id=s, project_id=p, preference_rank=rank
                )
                for s, p, rank in allocation
            ],
        )
        for number, allocation in enumerate(allocations, start=1)
    ]
    repositories.RunRepository().save_run(
        models.AssignmentRun(id=run_id, status="COMPLETED", solutions=solutions)
    )
    return [s.id for s in solutions]


def test_compare_two_alternatives(tmp_path: pathlib.Path) -> None:
    """Two alternatives of one run are compared without crashing."""
    client = _client(tmp_path)
    run = _engine_run(client)

    res = client.get(
        f"/compare?sol1={run.solutions[0].id}&sol2={run.solutions[1].id}"
    )

    assert res.status_code == 200
    assert b"Side-by-Side Solution Comparison" in res.data
    assert b"Trade-off Findings" in res.data
    assert b"Detailed Allocation Shifts" in res.data


def test_compare_link_without_parameters(tmp_path: pathlib.Path) -> None:
    """The menu link compares the first two alternatives of the latest run."""
    client = _client(tmp_path)
    _engine_run(client)

    res = client.get("/compare")

    assert res.status_code == 200
    assert b"Detailed Allocation Shifts" in res.data


def test_compare_with_one_solution_picks_a_partner(
    tmp_path: pathlib.Path,
) -> None:
    """The button on a solution page sends only sol1."""
    client = _client(tmp_path)
    run = _engine_run(client)

    res = client.get(f"/compare?sol1={run.solutions[1].id}")

    assert res.status_code == 200
    assert b"Detailed Allocation Shifts" in res.data


def test_compare_with_no_solutions(tmp_path: pathlib.Path) -> None:
    """An empty database gives guidance instead of an empty form."""
    client = _client(tmp_path)

    res = client.get("/compare")

    assert res.status_code == 200
    assert b"No solutions to compare yet" in res.data


def test_compare_unknown_solutions(tmp_path: pathlib.Path) -> None:
    """Unknown IDs (as in the supplied placeholder test) give a message."""
    client = _client(tmp_path)

    res = client.get("/compare?sol1=S1&sol2=S2")

    assert res.status_code == 200
    assert b"could not be found" in res.data


def test_compare_same_solution_twice(tmp_path: pathlib.Path) -> None:
    """Comparing a solution with itself says so plainly."""
    client = _client(tmp_path)
    run = _engine_run(client)
    sol = run.solutions[0].id

    res = client.get(f"/compare?sol1={sol}&sol2={sol}")

    assert b"are the same solution" in res.data
    assert b"Identical allocation outcomes" in res.data
    assert b"No student changes project" in res.data


def test_compare_shows_names_and_unranked_moves(
    tmp_path: pathlib.Path,
) -> None:
    """Names replace IDs, and a move outside preferences is labelled."""
    client = _client(tmp_path)
    _seed_small_cohort()
    sol_a, sol_b = _store_run(
        [
            [("S1", "P1", 1), ("S2", "P2", 2)],
            [("S1", "P2", None), ("S2", "P1", 1)],
        ]
    )

    res = client.get(f"/compare?sol1={sol_a}&sol2={sol_b}")

    assert res.status_code == 200
    assert b"Alice Chen" in res.data
    assert b"Bob Berg" in res.data
    assert b"Data Lakehouse" in res.data
    assert b"Now outside preferences" in res.data
    assert b"1 rank better" in res.data
    assert b"Choice #None" not in res.data


def test_compare_single_solution_run(tmp_path: pathlib.Path) -> None:
    """A run with one solution is reported honestly."""
    client = _client(tmp_path)
    _seed_small_cohort()
    (only,) = _store_run([[("S1", "P1", 1), ("S2", "P1", 1)]])

    res = client.get(f"/compare?sol1={only}")

    assert res.status_code == 200
    assert b"produced only one feasible solution" in res.data


def test_compare_across_runs_warns(tmp_path: pathlib.Path) -> None:
    """Solutions from different runs get a warning about changed inputs."""
    client = _client(tmp_path)
    _seed_small_cohort()
    (first,) = _store_run([[("S1", "P1", 1), ("S2", "P2", 2)]])
    (second,) = _store_run([[("S1", "P1", 1), ("S2", "P1", 1)]])

    res = client.get(f"/compare?sol1={first}&sol2={second}")

    assert b"come from different runs" in res.data
    assert b"Bob Berg" in res.data
