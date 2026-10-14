"""Unit tests for domain validation and feasibility checking."""

from app.domain import models
from app.domain import validation


def test_empty_cohort_validation() -> None:
    """Verifies that empty cohort data is flagged as invalid."""
    res = validation.validate_cohort(students=[], projects=[])
    assert res.is_valid is False
    assert any("Student cohort cannot be empty" in err for err in res.errors)
    assert any("Project catalog cannot be empty" in err for err in res.errors)


def test_duplicate_identifiers() -> None:
    """Verifies detection of duplicate student and project IDs."""
    students = [
        models.Student(id="S01", display_name="Student 1"),
        models.Student(id="S01", display_name="Student 1 Duplicate"),
    ]
    projects = [
        models.Project(id="P1", title="Project 1"),
        models.Project(id="P1", title="Project 1 Duplicate"),
    ]
    res = validation.validate_cohort(students=students, projects=projects)
    assert res.is_valid is False
    assert any("Duplicate student identifier" in err for err in res.errors)
    assert any("Duplicate project identifier" in err for err in res.errors)


def test_capacity_errors() -> None:
    """Verifies detection of negative, zero, or inverted capacities."""
    students = [models.Student(id="S01", display_name="Student 1")]
    projects = [
        models.Project(
            id="P1", title="Invalid Project", min_capacity=5, max_capacity=2
        )
    ]
    res = validation.validate_cohort(students=students, projects=projects)
    assert res.is_valid is False
    assert any("exceeding max capacity" in err for err in res.errors)


def test_contradictory_fixed_assignments() -> None:
    """Verifies detection of contradictory fixed assignments."""
    students = [
        models.Student(id="S01", display_name="S1"),
        models.Student(id="S02", display_name="S2"),
    ]
    projects = [
        models.Project(id="P1", title="P1", max_capacity=1),
        models.Project(id="P2", title="P2", max_capacity=2),
    ]
    # S01 fixed to both P1 and P2
    fixed = [
        models.FixedAssignment(student_id="S01", project_id="P1"),
        models.FixedAssignment(student_id="S01", project_id="P2"),
    ]
    res = validation.validate_cohort(
        students=students, projects=projects, fixed_assignments=fixed
    )
    assert res.is_valid is False
    assert any("Contradictory fixed assignment" in err for err in res.errors)


def test_fixed_exceeding_capacity() -> None:
    """Verifies that fixed assignments exceeding capacity cause error."""
    students = [
        models.Student(id="S01", display_name="S1"),
        models.Student(id="S02", display_name="S2"),
    ]
    projects = [
        models.Project(id="P1", title="P1", max_capacity=1),
    ]
    # 2 fixed assignments to P1 which has max_capacity 1
    fixed = [
        models.FixedAssignment(student_id="S01", project_id="P1"),
        models.FixedAssignment(student_id="S02", project_id="P1"),
    ]
    res = validation.validate_cohort(
        students=students, projects=projects, fixed_assignments=fixed
    )
    assert res.is_feasible is False
    assert any("exceed its maximum capacity" in err for err in res.errors)


def test_aggregate_capacity_deficit() -> None:
    """Verifies detection of aggregate capacity deficit."""
    students = [
        models.Student(id="S01", display_name="S1"),
        models.Student(id="S02", display_name="S2"),
        models.Student(id="S03", display_name="S3"),
    ]
    projects = [
        models.Project(id="P1", title="P1", max_capacity=2),
    ]
    # 3 students, but total capacity is only 2
    res = validation.validate_cohort(students=students, projects=projects)
    assert res.is_feasible is False
    assert any("Insufficient overall capacity" in err for err in res.errors)
