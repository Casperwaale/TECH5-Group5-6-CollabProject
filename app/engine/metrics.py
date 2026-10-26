"""Calculators for feasibility, efficiency, fairness, and trade-offs.

This module provides analytical functions to evaluate solutions according to
the requirements in Section 7 of the TECH5 specification.

Students (Team B) must implement these analytical functions to compute
student-project skill fit, Gini inequality, solution indicators, and
side-by-side trade-off comparisons.
"""

from typing import Any

from app.domain import models


def calculate_assignment_skill_fit(
    student: models.Student,
    project: models.Project,
) -> tuple[float, list[str]]:
    """Calculates skill fit score and unmet requirements for a student-project pair.

    In compliance with Section 7.2 of the TECH5 specification, skill fit
    evaluates how well the candidate student satisfies the required technical
    skills of the target project.

    The score is the mean of min(1, level / minimum_level) over the project's
    non-mandatory requirements; mandatory requirements are hard constraints
    and do not count (R4). A project without non-mandatory requirements gives
    1.0. The unmet list covers every requirement, mandatory or not, that the
    student is below, in the project's requirement order.

    Args:
        student: The student under evaluation.
        project: The project under evaluation.

    Returns:
        A tuple of (skill_fit_score [0.0, 1.0], list_of_unmet_skill_ids).
    """
    ratios = []
    unmet = []
    for req in project.requirements:
        level = student.get_skill_level(req.skill_id)
        if level < req.minimum_level:
            unmet.append(req.skill_id)
        if not req.is_mandatory:
            # minimum_level >= 1 is guaranteed by validation and the schema (R7)
            ratios.append(min(1.0, level / req.minimum_level))

    if not ratios:
        return 1.0, unmet
    return sum(ratios) / len(ratios), unmet


def calculate_gini(values: list[float]) -> float:
    """Calculates the Gini coefficient of inequality for non-negative values.

    In compliance with Section 7.3 of the TECH5 specification, the Gini
    coefficient measures the inequality/fairness in student preference rank
    distribution (0.0 represents perfect equality, 1.0 represents extreme inequality).

    Uses G = sum_i sum_j |r_i - r_j| / (2 * n * sum_i r_i) from the
    analytical note, section 3.3 (R9). An empty series or a series of only
    zeros has no inequality to measure and gives 0.0.

    Args:
        values: Non-negative numerical series (e.g. assigned preference ranks).

    Returns:
        The Gini coefficient in [0.0, 1.0].

    Raises:
        ValueError: If any value is negative.
    """
    if any(v < 0 for v in values):
        raise ValueError("Gini coefficient requires non-negative values")

    n = len(values)
    total = sum(values)
    # No students, or everyone at zero: perfect equality, and avoids 0/0
    if n == 0 or total == 0:
        return 0.0

    abs_diff_sum = sum(abs(a - b) for a in values for b in values)
    return abs_diff_sum / (2 * n * total)


def compute_solution_indicators(
    students: list[models.Student],
    projects: list[models.Project],
    assignments: list[models.Assignment],
    fixed_assignments: list[models.FixedAssignment] | None = None,
) -> dict[str, Any]:
    """Computes comprehensive feasibility, efficiency, and fairness indicators.

    Evaluates a solution across the four dimensions defined in the specification:
    1. Feasibility: Exact student count, capacity bounds, fixed assignments.
    2. Efficiency: Mean skill-fit score, unmet soft requirements count.
    3. Fairness: Rank distribution, mean rank, worst rank, unranked count, Gini.
    4. Capacity: Total assigned, total capacity, overall utilization, per-project.

    Args:
        students: Complete cohort of students.
        projects: Catalog of semester projects.
        assignments: List of student-to-project allocations.
        fixed_assignments: Optional list of locked pre-allocations.

    Returns:
        Dictionary containing structured indicators and diagnostic metrics:
        {
            "feasibility": {"is_feasible": bool, "violations": list[str], ...},
            "efficiency": {"mean_skill_fit": float, ...},
            "fairness": {"mean_rank": float, "worst_rank": int, "rank_gini": float, ...},
            "capacity": {"overall_utilization_pct": float, "projects": dict, ...}
        }

    Raises:
        NotImplementedError: To be implemented by Team B.
    """
    raise NotImplementedError(
        "TODO (Team B): Implement compute_solution_indicators"
    )


def compare_two_solutions(
    solution_a: models.Solution,
    solution_b: models.Solution,
) -> dict[str, Any]:
    """Performs detailed trade-off comparison between two alternative solutions.

    In compliance with Section 7.4 of the specification, identifies:
    - Changed student allocations between solutions A and B.
    - Improved and worsened student preference ranks.
    - Deltas in mean skill-fit, mean rank, and Gini coefficient.
    - Human-readable trade-off summary statements.

    Args:
        solution_a: Baseline solution.
        solution_b: Alternative solution to compare against A.

    Returns:
        Dictionary documenting differences, changed assignments, and trade-offs:
        {
            "solution_a_id": str,
            "solution_b_id": str,
            "is_distinct": bool,
            "changed_students_count": int,
            "changed_assignments": list[dict[str, Any]],
            "delta_metrics": dict[str, Any],
            "trade_off_summary": list[str]
        }
    """
    map_a = {a.student_id: a for a in solution_a.assignments}
    map_b = {b.student_id: b for b in solution_b.assignments}
    penalty = _penalty_rank(solution_a, solution_b)

    changed: list[dict[str, Any]] = []
    rank_improved = 0
    rank_worsened = 0
    for s_id in sorted(map_a.keys() & map_b.keys()):
        asg_a = map_a[s_id]
        asg_b = map_b[s_id]
        if asg_a.project_id == asg_b.project_id:
            continue

        # Unranked projects count as rank |P| + 1 (R14).
        r_a = asg_a.preference_rank if asg_a.preference_rank is not None else penalty
        r_b = asg_b.preference_rank if asg_b.preference_rank is not None else penalty
        if r_b < r_a:
            rank_change = "IMPROVED"
            rank_improved += 1
        elif r_b > r_a:
            rank_change = "WORSENED"
            rank_worsened += 1
        else:
            rank_change = "SAME"

        changed.append(
            {
                "student_id": s_id,
                "student_name": s_id,
                "project_a": asg_a.project_id,
                "project_a_id": asg_a.project_id,
                "project_a_title": asg_a.project_id,
                "rank_a": asg_a.preference_rank,
                "skill_fit_a": asg_a.skill_fit_score,
                "project_b": asg_b.project_id,
                "project_b_id": asg_b.project_id,
                "project_b_title": asg_b.project_id,
                "rank_b": asg_b.preference_rank,
                "skill_fit_b": asg_b.skill_fit_score,
                "rank_delta": r_b - r_a,
                "rank_change": rank_change,
            }
        )

    ind_a = solution_a.indicators or {}
    ind_b = solution_b.indicators or {}
    delta_metrics: dict[str, Any] = {
        "mean_skill_fit_delta": _indicator_delta(
            ind_a, ind_b, "efficiency", "mean_skill_fit"
        ),
        "mean_rank_delta": _indicator_delta(ind_a, ind_b, "fairness", "mean_rank"),
        "gini_delta": _indicator_delta(ind_a, ind_b, "fairness", "rank_gini"),
        "rank_variance_delta": _indicator_delta(
            ind_a, ind_b, "fairness", "rank_variance"
        ),
        "unranked_count_delta": _indicator_delta(
            ind_a, ind_b, "fairness", "unranked_count"
        ),
    }

    summary: list[str] = []
    if changed:
        summary.append(
            f"{len(changed)} student(s) are allocated to a different project "
            "in Solution B."
        )
    else:
        summary.append("Solutions A and B have identical allocations.")
    summary.append(
        f"{rank_improved} student(s) get a better-ranked project, "
        f"{rank_worsened} a worse-ranked one."
    )
    labels = {
        "mean_skill_fit_delta": "Mean skill fit",
        "mean_rank_delta": "Mean preference rank",
        "gini_delta": "Rank Gini coefficient",
    }
    for key, label in labels.items():
        delta = delta_metrics[key]
        if delta is None:
            summary.append(f"{label} change not available.")
        elif delta == 0:
            summary.append(f"{label} is unchanged.")
        else:
            direction = "increases" if delta > 0 else "decreases"
            summary.append(f"{label} {direction} by {abs(delta)} in Solution B.")

    mean_fit_delta = delta_metrics["mean_skill_fit_delta"]
    mean_rank_delta = delta_metrics["mean_rank_delta"]
    unranked_delta = delta_metrics["unranked_count_delta"]
    return {
        "solution_a_id": solution_a.id,
        "solution_a_alt": solution_a.alternative_number,
        "solution_b_id": solution_b.id,
        "solution_b_alt": solution_b.alternative_number,
        "is_distinct": len(changed) > 0,
        "changed_students_count": len(changed),
        "total_students": len(map_a.keys() | map_b.keys()),
        "changed_assignments": changed,
        "rank_improved_count": rank_improved,
        "rank_worsened_count": rank_worsened,
        "delta_metrics": delta_metrics,
        "delta_mean_skill_fit": mean_fit_delta if mean_fit_delta is not None else 0.0,
        "delta_mean_rank": mean_rank_delta if mean_rank_delta is not None else 0.0,
        "delta_unranked_count": (
            int(unranked_delta) if unranked_delta is not None else 0
        ),
        "trade_off_summary": summary,
    }


def _penalty_rank(
    solution_a: models.Solution,
    solution_b: models.Solution,
) -> int:
    """Returns the penalty rank |P| + 1 for unranked assignments (R14).

    |P| is read from the per-project capacity indicators. If neither solution
    has them, falls back to the largest rank seen in either solution plus one.

    Args:
        solution_a: Baseline solution.
        solution_b: Alternative solution.

    Returns:
        The rank assigned to a student placed on a project they did not rank.
    """
    for solution in (solution_a, solution_b):
        projects = (solution.indicators or {}).get("capacity", {}).get("projects")
        if projects:
            return len(projects) + 1
    ranks = [
        a.preference_rank
        for a in solution_a.assignments + solution_b.assignments
        if a.preference_rank is not None
    ]
    return max(ranks, default=0) + 1


def _indicator_delta(
    ind_a: dict[str, Any],
    ind_b: dict[str, Any],
    group: str,
    key: str,
    digits: int = 4,
) -> float | None:
    """Computes the rounded delta B minus A for one indicator.

    Args:
        ind_a: Indicators of the baseline solution.
        ind_b: Indicators of the alternative solution.
        group: Indicator group, e.g. "efficiency" or "fairness".
        key: Indicator key inside the group, e.g. "mean_rank".
        digits: Decimal places to round to.

    Returns:
        The rounded difference, or None if either value is missing.
    """
    value_a = ind_a.get(group, {}).get(key)
    value_b = ind_b.get(group, {}).get(key)
    if value_a is None or value_b is None:
        return None
    return round(value_b - value_a, digits)
