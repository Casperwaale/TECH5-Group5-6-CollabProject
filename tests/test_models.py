"""Unit tests for core object-oriented domain models."""

from app.domain import models


def test_skill_serialization() -> None:
    """Verifies Skill to_dict and from_dict roundtrip."""
    skill = models.Skill(
        id="py", name="Python", description="Programming in Python"
    )
    data = skill.to_dict()
    assert data["id"] == "py"
    assert data["name"] == "Python"

    restored = models.Skill.from_dict(data)
    assert restored.id == skill.id
    assert restored.name == skill.name
    assert restored.description == skill.description


def test_student_model_helpers() -> None:
    """Verifies Student model skill and preference query methods."""
    student = models.Student(
        id="S01",
        display_name="Alice",
        skills={"python": 3, "sql": 2},
        preferences=[
            models.Preference(student_id="S01", project_id="P1", rank=1),
            models.Preference(student_id="S01", project_id="P2", rank=2),
        ],
    )

    assert student.get_skill_level("python") == 3
    assert student.get_skill_level("sql") == 2
    assert student.get_skill_level("nonexistent") == 0

    assert student.get_preference_rank("P1") == 1
    assert student.get_preference_rank("P2") == 2
    assert student.get_preference_rank("P99") is None

    # Serialization roundtrip
    dict_repr = student.to_dict()
    restored = models.Student.from_dict(dict_repr)
    assert restored.id == "S01"
    assert restored.display_name == "Alice"
    assert restored.skills["python"] == 3
    assert len(restored.preferences) == 2


def test_project_model() -> None:
    """Verifies Project instantiation and requirement parsing."""
    project = models.Project(
        id="P1",
        title="AI Engine",
        min_capacity=1,
        max_capacity=4,
        requirements=[
            models.ProjectRequirement(
                project_id="P1",
                skill_id="ml",
                minimum_level=3,
                is_mandatory=True,
            )
        ],
    )
    assert project.max_capacity == 4
    assert len(project.requirements) == 1
    assert project.requirements[0].is_mandatory is True

    dict_repr = project.to_dict()
    restored = models.Project.from_dict(dict_repr)
    assert restored.id == "P1"
    assert restored.min_capacity == 1
    assert restored.max_capacity == 4
    assert restored.requirements[0].skill_id == "ml"


def test_solution_and_assignment() -> None:
    """Verifies Solution and Assignment entity serialization."""
    assignment = models.Assignment(
        student_id="S01",
        project_id="P1",
        is_fixed=True,
        preference_rank=1,
        skill_fit_score=0.85,
        unmet_requirements=["sql"],
    )
    solution = models.Solution(
        id="sol-1",
        run_id="run-1",
        alternative_number=1,
        strategy_name="PREFERENCE",
        objective_value=45.0,
        assignments=[assignment],
        indicators={"fairness": {"mean_rank": 1.0}},
    )

    assert solution.get_assignment_for_student("S01") is not None
    assert solution.get_assignment_for_student("S99") is None

    sol_dict = solution.to_dict()
    restored = models.Solution.from_dict(sol_dict)
    assert restored.id == "sol-1"
    assert restored.assignments[0].is_fixed is True
    assert restored.assignments[0].skill_fit_score == 0.85
