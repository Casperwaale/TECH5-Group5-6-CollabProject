"""Mathematical optimization solvers and Strategy Pattern skeleton for TECH5.

In compliance with Section 5 and Section 8 of the TECH5 specification,
Team B is responsible for proposing and implementing an approved assignment
method (e.g. Integer Linear Programming, heuristic search, or stable matching).

This module defines the abstract strategy base class and the AssignmentEngine
that implements AssignmentEngineContract.
"""

import abc
import logging
from typing import Any
import uuid

import pyomo.environ as pyo

from app.contract import contract
from app.domain import models
from app.domain import validation
from app.engine import metrics
from app.persistence import repositories

# Set up solver
solver_name = 'appsi_highs'
SOLVER = pyo.SolverFactory(solver_name)
SOLVER.options['threads'] = 1    # Extension: single thread, so ties are broken the same way every run (R16)


def prepare_data(
    students: list[models.Student],
    projects: list[models.Project],
    fixed_assignments: list[models.FixedAssignment] | None = None,
) -> dict[str, Any]:
    """Builds the sets and parameters of the ILP model as plain Python data.

    Follows docs/model/ilp_formulation.tex sections 1 and 2. Every quantity
    that is non-linear in the inputs (ranks, scores, skill fit) is computed
    here, so the model itself stays linear.

    Args:
        students: Students in the cohort.
        projects: Available semester projects.
        fixed_assignments: Pre-assigned student-project pairs that must hold.

    Returns:
        Dictionary with the index lists and parameter dicts keyed by tuples.
    """
    # --- Sets ---
    # Sorted identifiers, so identical input gives an identical model (R16)
    student_ids = sorted([student.id for student in students])    # S
    project_ids = sorted([project.id for project in projects])    # P
    student_by_id = {student.id: student for student in students}    # look up a student by id
    project_by_id = {project.id: project for project in projects}    # look up a project by id
    n = len(student_ids)    # |S|, number of students
    m = len(project_ids)    # |P|, number of projects

    # F: fixed (locked) student-project pairs (R3)
    fixed_pairs = []
    if fixed_assignments is not None:
        fixed_pairs = [(fixed.student_id, fixed.project_id) for fixed in fixed_assignments]

    # E_p: mandatory skills of each project; only projects that have one are stored
    # Q_{p,t}: students whose level meets the required level of mandatory skill t on project p (R13)
    mandatory_skills = {}
    qualified = {}
    for p in project_ids:
        for req in project_by_id[p].requirements:
            if req.is_mandatory:
                if p not in mandatory_skills:
                    mandatory_skills[p] = []
                mandatory_skills[p].append(req.skill_id)
                qualified[p, req.skill_id] = []
                for s in student_ids:
                    if student_by_id[s].get_skill_level(req.skill_id) >= req.minimum_level:
                        qualified[p, req.skill_id].append(s)
    for p in mandatory_skills:
        mandatory_skills[p] = sorted(mandatory_skills[p])
    mandatory_projects = sorted(mandatory_skills.keys())    # P^E, projects with a mandatory requirement

    # --- Parameters ---
    min_capacity = {p: project_by_id[p].min_capacity for p in project_ids}    # l_p
    max_capacity = {p: project_by_id[p].max_capacity for p in project_ids}    # u_p

    # r_{s,p}: stated rank, or penalty rank m + 1 for an unranked project (eq. 1, R14)
    rank = {
        (s, p): student_by_id[s].get_preference_rank(p)
        if student_by_id[s].get_preference_rank(p) is not None else m + 1
        for s in student_ids for p in project_ids
    }

    # phi_{s,p}: preference score, 1 for a first choice, 0 for an unranked project (eq. 2)
    preference_score = {
        (s, p): (m + 1 - rank[s, p]) / m
        for s in student_ids for p in project_ids
    }

    # sigma_{s,p}: skill fit over non-mandatory requirements (eq. 3, R4); same function as the metrics
    # The same call also lists the requirements the student is below, stored for the results
    skill_fit = {}
    unmet_requirements = {}
    for s in student_ids:
        for p in project_ids:
            score, unmet = metrics.calculate_assignment_skill_fit(student_by_id[s], project_by_id[p])
            skill_fit[s, p] = score
            unmet_requirements[s, p] = unmet

    return {
        "student_ids": student_ids,
        "project_ids": project_ids,
        "n": n,
        "m": m,
        "fixed_pairs": fixed_pairs,
        "mandatory_skills": mandatory_skills,
        "mandatory_projects": mandatory_projects,
        "qualified": qualified,
        "min_capacity": min_capacity,
        "max_capacity": max_capacity,
        "rank": rank,
        "preference_score": preference_score,
        "skill_fit": skill_fit,
        "unmet_requirements": unmet_requirements,
    }


def build_model(
    data: dict[str, Any],
    excluded_solutions: list[list[tuple[str, str]]] | None = None,
) -> pyo.ConcreteModel:
    """Builds the variables and hard constraints shared by every strategy.

    Follows docs/model/ilp_formulation.tex sections 3 and 4. The objective is
    not added here: each strategy adds its own, so the base model is written
    once and only the objective changes.

    Args:
        data: Sets and parameters from prepare_data.
        excluded_solutions: Earlier solutions as lists of (student, project)
            pairs; each one gets a no-good cut so the new solution differs.

    Returns:
        The Pyomo model with variables x and y and constraints (5) to (10).
    """
    student_ids = data["student_ids"]
    project_ids = data["project_ids"]
    mandatory_projects = data["mandatory_projects"]

    model = pyo.ConcreteModel('Student-project assignment')

    # Decision variables
    # x[s,p] = 1 if student s is assigned to project p, 0 otherwise (eq. 4)
    model.x = pyo.Var(student_ids, project_ids, domain=pyo.Binary)
    # y[p] = 1 if project p is used, 0 otherwise; only projects with a mandatory skill (eq. 5)
    model.y = pyo.Var(mandatory_projects, domain=pyo.Binary)

    # Constraint (7): each student is assigned to exactly one project (R1)
    model.one_project_constraint = pyo.ConstraintList()
    for s in student_ids:
        model.one_project_constraint.add(
            sum(model.x[s, p] for p in project_ids) == 1
        )

    # Constraint (8): headcount of each project between its minimum and maximum (R1)
    model.lower_bound_constraint = pyo.ConstraintList()
    for p in project_ids:
        model.lower_bound_constraint.add(
            sum(model.x[s, p] for s in student_ids) >= data["min_capacity"][p]
        )

    model.upper_bound_constraint = pyo.ConstraintList()
    for p in project_ids:
        model.upper_bound_constraint.add(
            sum(model.x[s, p] for s in student_ids) <= data["max_capacity"][p]
        )

    # Constraint (9): fixed assignments always hold (R3)
    model.fixed_constraint = pyo.ConstraintList()
    for s, p in data["fixed_pairs"]:
        model.fixed_constraint.add(
            model.x[s, p] == 1
        )

    # Constraint (10): a used project has at least one qualified student per mandatory skill (R13)
    model.mandatory_constraint = pyo.ConstraintList()
    for p in mandatory_projects:
        for t in data["mandatory_skills"][p]:
            model.mandatory_constraint.add(
                sum(model.x[s, p] for s in data["qualified"][p, t]) >= model.y[p]
            )

    # Constraint (11): a project with any student counts as used; u_p is the tightest big-M (R13)
    model.used_constraint = pyo.ConstraintList()
    for p in mandatory_projects:
        model.used_constraint.add(
            sum(model.x[s, p] for s in student_ids) <= data["max_capacity"][p] * model.y[p]
        )

    # Constraint (12): no-good cut, at least one student moves compared with each earlier solution (R5)
    model.no_good_constraint = pyo.ConstraintList()
    if excluded_solutions is not None:
        for solution in excluded_solutions:
            model.no_good_constraint.add(
                sum(model.x[s, p] for s, p in solution) <= data["n"] - 1
            )

    return model


def solve_model(model: pyo.ConcreteModel) -> str:
    """Solves the model with HiGHS and reports the outcome instead of raising.

    A bare SOLVER.solve(model) raises RuntimeError on an infeasible model.
    Infeasibility is a valid result here (R2, R10), so it is returned as a
    status and the caller decides what to report.

    Args:
        model: A built model with an objective.

    Returns:
        "OPTIMAL" with the solution loaded into the model, "INFEASIBLE",
        "SOLVER_UNAVAILABLE", or the solver's own termination condition.
    """
    if not SOLVER.available():
        return "SOLVER_UNAVAILABLE"

    # Extension: load_solutions=False + termination check, so infeasibility is reported instead of raising
    results = SOLVER.solve(model, load_solutions=False)
    condition = results.solver.termination_condition

    if condition == pyo.TerminationCondition.optimal:
        model.solutions.load_from(results)
        return "OPTIMAL"
    # Every objective is bounded (binary x), so the model is never unbounded: both conditions mean infeasible
    if condition == pyo.TerminationCondition.infeasible:
        return "INFEASIBLE"
    if condition == pyo.TerminationCondition.infeasibleOrUnbounded:
        return "INFEASIBLE"
    return str(condition).upper()


def read_assignments(
    model: pyo.ConcreteModel, data: dict[str, Any]
) -> list[models.Assignment]:
    """Reads the solved x values back into Assignment objects.

    Args:
        model: A model solved with status "OPTIMAL".
        data: Sets and parameters from prepare_data.

    Returns:
        One Assignment per student, in sorted student order.
    """
    assignments = []
    for s in data["student_ids"]:
        for p in data["project_ids"]:
            if pyo.value(model.x[s, p]) > 0.5:
                assignments.append(models.Assignment(
                    student_id=s,
                    project_id=p,
                    is_fixed=(s, p) in data["fixed_pairs"],
                    # Unranked projects carry the penalty rank m + 1 in the model, but None here (R14)
                    preference_rank=data["rank"][s, p] if data["rank"][s, p] <= data["m"] else None,
                    skill_fit_score=data["skill_fit"][s, p],
                    unmet_requirements=data["unmet_requirements"][s, p],
                ))
    return assignments


class AssignmentStrategy(abc.ABC):
    """Abstract Base Class for student-to-project allocation strategies.

    Team B should derive concrete strategy subclasses implementing specific
    objective functions (e.g. preference satisfaction, skill fit, balanced).
    Every strategy shares the model of build_model; a strategy only supplies
    its objective coefficient per student-project pair and the sense.
    """

    sense = pyo.minimize    # Objective direction; each subclass sets its own

    def __init__(self, name: str, description: str) -> None:
        """Initializes the strategy with descriptive metadata.

        Args:
            name: Machine-readable identifier for the strategy.
            description: Human-readable explanation of the objective function.
        """
        self.name = name
        self.description = description

    @abc.abstractmethod
    def calculate_cost_or_utility(
        self,
        data: dict[str, Any],
        s: str,
        p: str,
    ) -> float:
        """Computes the objective coefficient for assigning student s to project p.

        Reads the parameters from prepare_data instead of recomputing them from
        the Student and Project objects, because the tie-break weights need the
        cohort size n and the penalty rank needs the project count m (D14).

        Args:
            data: Sets and parameters from prepare_data.
            s: Student identifier.
            p: Project identifier.

        Returns:
            The coefficient of x[s,p] in this strategy's objective.
        """

    def solve(
        self,
        students: list[models.Student],
        projects: list[models.Project],
        fixed_assignments: list[models.FixedAssignment] | None = None,
        excluded_solutions: list[list[tuple[str, str]]] | None = None,
    ) -> tuple[str, list[models.Assignment], float | None, dict[str, Any]]:
        """Solves the assignment problem under this strategy's formulation.

        In accordance with Section 8 of the specification, must:
        - Assign students to projects respecting capacities [min_cap, max_cap].
        - Enforce each student receives exactly one project allocation.
        - Strictly preserve pre-allocated fixed assignments.
        - Support integer no-good cuts (excluded_solutions) to guarantee distinct
          Pareto alternatives.

        Args:
            students: List of students in the cohort.
            projects: List of available semester projects.
            fixed_assignments: Pre-assigned student-project pairs that must hold.
            excluded_solutions: Previous solution allocations to cut out.

        Returns:
            A tuple of (solver_status, assignments, objective_value, diagnostics).
            On any status other than "OPTIMAL" the assignments are empty and
            the objective value is None.
        """
        data = prepare_data(students, projects, fixed_assignments)
        model = build_model(data, excluded_solutions)

        # Objective: sum over all pairs of (this strategy's coefficient) * x[s,p].
        # The coefficient already includes the strategy's tie-break term, e.g.
        # Preference returns r - epsilon * sigma, so this sum is exactly Z_pref.
        model.objective = pyo.Objective(
            expr = sum(
                self.calculate_cost_or_utility(data, s, p) * model.x[s, p]
                for s in data["student_ids"] for p in data["project_ids"]
            ),
            sense = self.sense
        )

        status = solve_model(model)
        diagnostics = {
            "solver_status": status,
            "variables_count": model.nvariables(),
            "constraints_count": model.nconstraints(),
        }
        if status != "OPTIMAL":
            return status, [], None, diagnostics
        return status, read_assignments(model, data), pyo.value(model.objective), diagnostics


class PreferenceOrientedSolver(AssignmentStrategy):
    """Strategy 1: minimise the total preference rank; skill fit breaks ties."""

    sense = pyo.minimize

    def __init__(self) -> None:
        """Initializes the preference strategy."""
        super().__init__(
            name="PREFERENCE",
            description="Minimise the total preference rank; skill fit breaks ties.",
        )

    def calculate_cost_or_utility(self, data: dict[str, Any], s: str, p: str) -> float:
        """Returns r[s,p] - epsilon_pref * sigma[s,p] (Z_pref).

        Args:
            data: Sets and parameters from prepare_data.
            s: Student identifier.
            p: Project identifier.

        Returns:
            The coefficient of x[s,p] in Z_pref.
        """
        # Tie-break weight: the skill term totals at most n / (n + 1) < 1, so it never outweighs one rank step
        epsilon_pref = 1 / (data["n"] + 1)
        return data["rank"][s, p] - epsilon_pref * data["skill_fit"][s, p]


class SkillFitOrientedSolver(AssignmentStrategy):
    """Strategy 2: maximise the total skill fit; preference breaks ties."""

    sense = pyo.maximize

    def __init__(self) -> None:
        """Initializes the skill-fit strategy."""
        super().__init__(
            name="SKILL_FIT",
            description="Maximise the total skill fit; preference breaks ties.",
        )

    def calculate_cost_or_utility(self, data: dict[str, Any], s: str, p: str) -> float:
        """Returns sigma[s,p] + epsilon_skill * phi[s,p] (Z_skill).

        Args:
            data: Sets and parameters from prepare_data.
            s: Student identifier.
            p: Project identifier.

        Returns:
            The coefficient of x[s,p] in Z_skill.
        """
        # Tie-break weight: the preference term totals at most 10^-3, a practical (not exact) priority
        epsilon_skill = 1e-3 / data["n"]
        return data["skill_fit"][s, p] + epsilon_skill * data["preference_score"][s, p]


class AssignmentEngine(contract.AssignmentEngineContract):
    """Main Assignment Engine orchestrating validation, execution, and persistence.

    Implements the internal component contract (AssignmentEngineContract)
    connecting Component B to Component A.
    """

    def __init__(
        self, run_repo: repositories.RunRepository | None = None
    ) -> None:
        """Initializes the AssignmentEngine with persistence repositories.

        Args:
            run_repo: Optional repository for persisting runs and solutions.
        """
        self.run_repo = (
            run_repo if run_repo is not None else repositories.RunRepository()
        )
        self.strategies: dict[str, AssignmentStrategy] = {
            # Team B: Instantiate and register your custom strategies here
        }

    def validate_inputs(
        self, request: contract.RunRequest
    ) -> contract.ValidationOutcome:
        """Validates cohort and constraints before attempting optimization.

        Args:
            request: The run request containing students, projects, etc.

        Returns:
            ValidationOutcome with validity, feasibility, errors, and warnings.
        """
        val_result = validation.validate_cohort(
            students=request.students,
            projects=request.projects,
            skills=request.skills,
            fixed_assignments=request.fixed_assignments,
        )
        return contract.ValidationOutcome(
            is_valid=val_result.is_valid,
            is_feasible=val_result.is_feasible,
            errors=list(val_result.errors),
            warnings=list(val_result.warnings),
            infeasibility_reasons=list(val_result.infeasibility_reasons),
        )

    def execute_run(
        self, request: contract.RunRequest
    ) -> models.AssignmentRun:
        """Executes the assignment algorithm, calculates metrics, and persists run.

        In accordance with Section 8 of the specification, Team B must:
        1. Synchronize entities to maintain relational integrity.
        2. Validate cohort feasibility.
        3. Run assignment solver(s) to generate one or more distinct alternatives.
        4. Calculate indicators for each alternative using app.engine.metrics.
        5. Persist run and solutions via self.run_repo.
        6. Return populated models.AssignmentRun.

        Args:
            request: The run request containing students, projects, etc.

        Returns:
            The created AssignmentRun populated with alternative solutions.

        Raises:
            NotImplementedError: To be implemented by Team B.
        """
        raise NotImplementedError(
            "TODO (Team B): Implement execute_run in app/engine/solvers.py"
        )

    def run_assignment(
        self,
        students: list[models.Student],
        projects: list[models.Project],
        skills: list[models.Skill] | None = None,
        fixed_assignments: list[models.FixedAssignment] | None = None,
        strategy_name: str = "PREFERENCE",
        max_alternatives: int = 3,
        notes: str = "",
    ) -> models.AssignmentRun:
        """Convenience method delegating to execute_run via RunRequest.

        Args:
            students: Student profiles.
            projects: Project specifications.
            skills: Optional skills catalog.
            fixed_assignments: Optional pre-allocated locks.
            strategy_name: Strategy key name.
            max_alternatives: Max solutions to generate.
            notes: Administrative description or notes for the run.

        Returns:
            The created AssignmentRun.
        """
        req = contract.RunRequest(
            students=students,
            projects=projects,
            skills=skills or [],
            fixed_assignments=fixed_assignments or [],
            strategy_key=strategy_name,
            max_alternatives=max_alternatives,
            notes=notes,
        )
        return self.execute_run(req)

    def list_runs(self, limit: int = 20) -> list[models.AssignmentRun]:
        """Retrieves historical assignment runs from repository.

        Args:
            limit: Maximum number of runs to retrieve.

        Returns:
            List of historical AssignmentRun domain objects.
        """
        return self.run_repo.list_runs(limit=limit)

    def get_run(self, run_id: str) -> models.AssignmentRun | None:
        """Retrieves a specific run by identifier.

        Args:
            run_id: Unique run identifier.

        Returns:
            The AssignmentRun object, or None if not found.
        """
        return self.run_repo.get_run(run_id)

    def get_solution(self, solution_id: str) -> models.Solution | None:
        """Retrieves a specific solution and its student allocations.

        Args:
            solution_id: Unique solution identifier.

        Returns:
            The Solution object with assignments, or None if not found.
        """
        return self.run_repo.get_solution(solution_id)

    def compare_solutions(
        self, solution_a_id: str, solution_b_id: str
    ) -> models.RunComparison:
        """Compares two alternative solutions side-by-side using metrics module.

        Args:
            solution_a_id: Identifier of the baseline solution.
            solution_b_id: Identifier of the comparison solution.

        Returns:
            RunComparison containing delta metrics and changed assignments.

        Raises:
            KeyError: If either solution cannot be found.
        """
        sol_a = self.run_repo.get_solution(solution_a_id)
        sol_b = self.run_repo.get_solution(solution_b_id)
        if sol_a is None or sol_b is None:
            raise KeyError(
                f"Solutions not found: {solution_a_id}, {solution_b_id}"
            )
        comp_dict = metrics.compare_two_solutions(sol_a, sol_b)
        return models.RunComparison.from_dict(comp_dict)
