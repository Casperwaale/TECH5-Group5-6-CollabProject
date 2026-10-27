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


def test_duplicate_preference_rank_is_invalid() -> None:
    """A student cannot give two different projects the same rank."""
    student = models.Student(
        id="S01", display_name="Student 1",
        preferences=[
            models.Preference(student_id="S01", project_id="P1", rank=1),
            models.Preference(student_id="S01", project_id="P2", rank=1),
        ],
    )
    projects = [
        models.Project(id="P1", title="Project 1"),
        models.Project(id="P2", title="Project 2"),
    ]
    result = validation.validate_cohort([student], projects)
    assert not result.is_valid
    assert any("duplicate rank" in error for error in result.errors)


def test_invalid_student_skill_levels_are_rejected() -> None:
    """Reported proficiency must be an integer between one and five."""
    projects = [models.Project(id="P1", title="Project 1")]
    for bad_level in (0, 6, -1, 2.5, True):
        student = models.Student(
            id="S01", display_name="Student 1", skills={"python": bad_level}
        )
        result = validation.validate_cohort([student], projects)
        assert not result.is_valid
        assert any("invalid skill level" in error for error in result.errors)


def test_valid_student_skill_levels_are_accepted() -> None:
    projects = [models.Project(id="P1", title="Project 1")]
    for good_level in (1, 2, 3, 4, 5):
        student = models.Student(
            id="S01", display_name="Student 1", skills={"python": good_level}
        )
        result = validation.validate_cohort([student], projects)
        assert result.is_valid


def test_fewer_than_three_preferences_warns_without_rejecting() -> None:
    projects = [models.Project(id=f"P{i}", title=f"Project {i}") for i in range(1, 4)]
    student = models.Student(
        id="S01", display_name="Student 1",
        preferences=[models.Preference(student_id="S01", project_id="P1", rank=1)],
    )
    result = validation.validate_cohort([student], projects)
    assert result.is_valid
    assert any("fewer than 3 projects" in warning for warning in result.warnings)


def test_three_preferences_does_not_trigger_short_ranking_warning() -> None:
    projects = [models.Project(id=f"P{i}", title=f"Project {i}") for i in range(1, 4)]
    student = models.Student(
        id="S01", display_name="Student 1",
        preferences=[models.Preference(student_id="S01", project_id=f"P{i}", rank=i)
                     for i in range(1, 4)],
    )
    result = validation.validate_cohort([student], projects)
    assert not any("fewer than 3 projects" in warning for warning in result.warnings)

def test_duplicate_preferred_project_is_invalid() -> None:
    """A student cannot rank the same project more than once."""
    student = models.Student(
        id="S01", display_name="Student 1",
        preferences=[
            models.Preference(student_id="S01", project_id="P1", rank=1),
            models.Preference(student_id="S01", project_id="P1", rank=2),
        ],
    )
    projects = [models.Project(id="P1", title="Project 1")]

    result = validation.validate_cohort([student], projects)

    assert not result.is_valid
    assert any("multiple preferences for project 'P1'" in error
               for error in result.errors)



def test_invalid_requirement_levels_are_rejected() -> None:
    """A project's required level must be an integer between one and five (R7)."""
    for bad_level in (0, 6, -1, 2.5, True):
        project = models.Project(
            id="P1",
            title="Project 1",
            requirements=[
                models.ProjectRequirement("P1", "python", minimum_level=bad_level)
            ],
        )
        result = validation.validate_cohort([], [project])
        assert not result.is_valid
        assert any("requires invalid level" in error for error in result.errors)


def test_valid_requirement_levels_are_accepted() -> None:
    """Required levels one to five raise no level error."""
    for level in range(1, 6):
        project = models.Project(
            id="P1",
            title="Project 1",
            requirements=[models.ProjectRequirement("P1", "python", minimum_level=level)],
        )
        student = models.Student(
            id="S01",
            display_name="Student 1",
            preferences=[models.Preference("S01", "P1", 1)],
        )
        result = validation.validate_cohort([student], [project])
        assert not any("requires invalid level" in error for error in result.errors)


def test_ranks_below_one_are_rejected() -> None:
    """Preference ranks start at one (R12, schema CHECK rank >= 1)."""
    projects = [models.Project(id="P1", title="Project 1")]
    for bad_rank in (0, -2):
        student = models.Student(
            id="S01",
            display_name="Student 1",
            preferences=[models.Preference("S01", "P1", bad_rank)],
        )
        result = validation.validate_cohort([student], projects)
        assert not result.is_valid
        assert any("invalid rank" in error for error in result.errors)


def test_same_lock_twice_is_reported_as_duplicate() -> None:
    """The same lock listed twice is a duplicate, not a contradiction."""
    projects = [models.Project(id="P1", title="Project 1", max_capacity=1)]
    student = models.Student(
        id="S01",
        display_name="Student 1",
        preferences=[models.Preference("S01", "P1", 1)],
    )
    lock = models.FixedAssignment(student_id="S01", project_id="P1")
    result = validation.validate_cohort([student], projects, [], [lock, lock])
    assert not result.is_valid
    assert any("Duplicate fixed assignment" in error for error in result.errors)
    assert not any("Contradictory" in error for error in result.errors)
    # Counted once, so a one-seat project is not reported as over capacity
    assert result.is_feasible
