"""Benchmark datasets and demonstration scenarios for TECH5.

This module provides reproducible test cohorts illustrating distinct trade-offs,
fixed allocations, capacity bottlenecks, and infeasible conditions.
"""

from typing import Any

from app.domain import models


def get_skills_catalog() -> list[models.Skill]:
    """Provides a foundational skill catalog for semester cohorts.

    Returns:
        List of Skill instances.
    """
    return [
        models.Skill(
            id="python",
            name="Python Programming",
            description="Core Python, OOP, algorithms, and modular design.",
        ),
        models.Skill(
            id="sql",
            name="SQL & Data Modeling",
            description=(
                "Relational database design, normalisation, and complex "
                "queries."
            ),
        ),
        models.Skill(
            id="ml",
            name="Machine Learning",
            description=(
                "Supervised/unsupervised models, scikit-learn, evaluation "
                "metrics."
            ),
        ),
        models.Skill(
            id="web",
            name="Full-Stack Web Dev",
            description=(
                "Flask/FastAPI, REST APIs, HTML5/CSS, clientside integration."
            ),
        ),
        models.Skill(
            id="fintech",
            name="Financial Modeling",
            description=(
                "Valuation, econometric analysis, and quantitative risk "
                "modeling."
            ),
        ),
    ]


def get_standard_scenario() -> dict[str, Any]:
    """Generates a realistic standard cohort with trade-offs.

    Returns:
        Dictionary with students, projects, skills, and fixed_assignments.
    """
    skills = get_skills_catalog()

    projects = [
        models.Project(
            id="P1",
            title="Sustainable FinTech Risk Engine",
            description=(
                "ESG analytics and quantitative risk scoring in banking."
            ),
            min_capacity=1,
            max_capacity=3,
            requirements=[
                models.ProjectRequirement(
                    project_id="P1",
                    skill_id="fintech",
                    minimum_level=3,
                    is_mandatory=False,
                ),
                models.ProjectRequirement(
                    project_id="P1",
                    skill_id="python",
                    minimum_level=2,
                    is_mandatory=False,
                ),
            ],
        ),
        models.Project(
            id="P2",
            title="Cloud Data Pipeline & Lakehouse",
            description="Scalable ELT pipelines, SQL data warehouse modeling.",
            min_capacity=1,
            max_capacity=3,
            requirements=[
                models.ProjectRequirement(
                    project_id="P2",
                    skill_id="sql",
                    minimum_level=3,
                    is_mandatory=False,
                ),
                models.ProjectRequirement(
                    project_id="P2",
                    skill_id="python",
                    minimum_level=2,
                    is_mandatory=False,
                ),
            ],
        ),
        models.Project(
            id="P3",
            title="Healthcare Predictive ML Assistant",
            description=(
                "Clinical time-series prediction and medical diagnostic ML."
            ),
            min_capacity=1,
            max_capacity=3,
            requirements=[
                models.ProjectRequirement(
                    project_id="P3",
                    skill_id="ml",
                    minimum_level=3,
                    is_mandatory=False,
                ),
                models.ProjectRequirement(
                    project_id="P3",
                    skill_id="python",
                    minimum_level=3,
                    is_mandatory=False,
                ),
            ],
        ),
        models.Project(
            id="P4",
            title="Smart City Mobility Portal",
            description=(
                "Interactive web decision dashboard for municipal transit."
            ),
            min_capacity=1,
            max_capacity=3,
            requirements=[
                models.ProjectRequirement(
                    project_id="P4",
                    skill_id="web",
                    minimum_level=3,
                    is_mandatory=False,
                ),
                models.ProjectRequirement(
                    project_id="P4",
                    skill_id="python",
                    minimum_level=1,
                    is_mandatory=False,
                ),
            ],
        ),
    ]

    # 10 Students with complementary proficiencies and conflicting preferences
    raw_students = [
        (
            "S01",
            "Alice Chen",
            {"python": 4, "ml": 4, "sql": 3},
            ["P3", "P2", "P1"],
        ),
        (
            "S02",
            "Bob Smith",
            {"fintech": 4, "python": 2, "sql": 2},
            ["P1", "P4", "P2"],
        ),
        (
            "S03",
            "Clara Holm",
            {"sql": 4, "web": 3, "python": 3},
            ["P2", "P4", "P3"],
        ),
        (
            "S04",
            "David Nygard",
            {"web": 4, "python": 3, "sql": 2},
            ["P4", "P3", "P2"],
        ),
        (
            "S05",
            "Emma Lind",
            {"python": 3, "fintech": 3, "ml": 2},
            ["P1", "P3", "P4"],
        ),
        (
            "S06",
            "Fredrik Berg",
            {"sql": 3, "ml": 3, "python": 2},
            ["P3", "P2", "P1"],
        ),
        (
            "S07",
            "Greta Hansen",
            {"web": 3, "sql": 3, "python": 1},
            ["P4", "P2", "P1"],
        ),
        (
            "S08",
            "Henrik Olsen",
            {"fintech": 3, "python": 3, "sql": 3},
            ["P1", "P2", "P3"],
        ),
        (
            "S09",
            "Ingrid Solberg",
            {"ml": 4, "python": 4, "sql": 2},
            ["P3", "P1", "P4"],
        ),
        (
            "S10",
            "Jonas Dale",
            {"web": 4, "sql": 2, "python": 2},
            ["P4", "P1", "P2"],
        ),
    ]

    students = [
        models.Student(
            id=s_id,
            display_name=name,
            skills=sk,
            preferences=[
                models.Preference(
                    student_id=s_id, project_id=p_id, rank=idx + 1
                )
                for idx, p_id in enumerate(prefs)
            ],
        )
        for s_id, name, sk, prefs in raw_students
    ]

    return {
        "scenario_name": "Standard Cohort (Trade-off Benchmark)",
        "description": (
            "10 students, 4 projects (capacity 3 each). Produces 3 distinct "
            "Pareto solutions."
        ),
        "skills": skills,
        "projects": projects,
        "students": students,
        "fixed_assignments": [],
    }


def get_fixed_assignment_scenario() -> dict[str, Any]:
    """Provides a cohort demonstrating the exact effect of fixed constraints.

    Returns:
        Dictionary with student, project, and locked assignment data.
    """
    base = get_standard_scenario()
    base["scenario_name"] = "Fixed Assignment & Impact Scenario"
    base["description"] = (
        "Locks student S02 to project P2 (despite P1 being 1st choice) to "
        "illustrate re-allocation and guarantee of fixed constraints."
    )
    base["fixed_assignments"] = [
        models.FixedAssignment(
            student_id="S02",
            project_id="P2",
            status="APPROVED",
            reason=(
                "Pre-arranged research grant fellowship on cloud data "
                "pipelines."
            ),
        )
    ]
    return base


def get_infeasible_scenario() -> dict[str, Any]:
    """Generates an infeasible scenario due to aggregate capacity deficit.

    Returns:
        Dictionary with an overconstrained configuration.
    """
    base = get_standard_scenario()
    base["scenario_name"] = "Capacity Deficit (Infeasible Scenario)"
    base["description"] = (
        "Reduces project capacities so total capacity (6) is strictly less "
        "than student count (10), demonstrating clear mathematical "
        "infeasibility diagnostics."
    )
    # Total capacity = 2 + 2 + 1 + 1 = 6 < 10 students
    for p in base["projects"]:
        p.max_capacity = 2 if p.id in ("P1", "P2") else 1
    return base


def get_conflicting_fixed_scenario() -> dict[str, Any]:
    """Generates an invalid scenario with contradictory fixed constraints.

    Returns:
        Dictionary with contradictory fixed assignment data.
    """
    base = get_standard_scenario()
    base["scenario_name"] = "Contradictory Fixed Assignments (Invalid Scenario)"
    base["description"] = (
        "Assigns 4 fixed students to Project P1 (which has max capacity 3), "
        "demonstrating validation error reporting."
    )
    base["fixed_assignments"] = [
        models.FixedAssignment(
            student_id="S01", project_id="P1", reason="Lock 1"
        ),
        models.FixedAssignment(
            student_id="S02", project_id="P1", reason="Lock 2"
        ),
        models.FixedAssignment(
            student_id="S05", project_id="P1", reason="Lock 3"
        ),
        models.FixedAssignment(
            student_id="S08", project_id="P1", reason="Lock 4"
        ),
    ]
    return base
