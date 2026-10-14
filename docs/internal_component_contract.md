# Deliverable 4: Internal Component Contract & Integration Specification

## 1. Architectural Agreement & Scope

In accordance with Section 8 of the TECH5 Project Specification, the interaction between **Component A** (*Visualization and Recommendation Component*) and **Component B** (*Assignment Engine*) is governed by an explicit in-process Python contract.

```
+-------------------------------------------------------------------------+
|                                                                         |
|            COMPONENT A: VISUALIZATION & RECOMMENDATION                  |
|    - Dashboard, Cohort CRUD, Scenarios, Solution Views, Recommendations |
|                                                                         |
+-------------------------------------------------------------------------+
                                    |
                                    | Python Method Invocations
                                    | (contract.AssignmentEngineContract)
                                    v
+-------------------------------------------------------------------------+
|                                                                         |
|                     INTERNAL COMPONENT CONTRACT                         |
|         app/contract/contract.py: AssignmentEngineContract             |
|   - validate_inputs(request: RunRequest) -> ValidationOutcome          |
|   - execute_run(request: RunRequest) -> AssignmentRun                   |
|   - list_runs(limit: int) -> list[AssignmentRun]                        |
|   - get_run(run_id: str) -> AssignmentRun | None                        |
|   - get_solution(solution_id: str) -> Solution | None                   |
|   - compare_solutions(sol_a_id: str, sol_b_id: str) -> RunComparison   |
|                                                                         |
+-------------------------------------------------------------------------+
                                    ^
                                    | Implements Abstract Contract
                                    |
+-------------------------------------------------------------------------+
|                                                                         |
|                     COMPONENT B: ASSIGNMENT ENGINE                      |
|           app/engine/solvers.py: AssignmentEngine                       |
|   - Strategy Pattern: PREFERENCE, SKILL_FIT, BALANCED                   |
|   - PuLP Integer Linear Programming & Pareto No-Good Cuts               |
|   - Analytical Indicators (Gini, Mean Rank, Skill Fit, Utilization)     |
|                                                                         |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                   SHARED RELATIONAL PERSISTENCE                         |
|                      SQLite 3NF Schema (app/persistence)                |
+-------------------------------------------------------------------------+
```

This design guarantees complete decoupling:
1. **Zero Network Overhead**: Eliminates serialization latency, HTTP status code translation, connection timeouts, and port conflicts.
2. **Type Safety & Compiler Diagnostics**: All DTOs and return types are fully type-annotated (`typing` and Python 3.10+ union types).
3. **Independent Testability**: Component B can be tested completely headlessly without web servers, and Component A can be tested with mock engine implementations.

---

## 2. Shared Data Definitions & Identifiers

All entities share standardized identifiers across both components:

| Entity | Identifier Format | Definition |
|---|---|---|
| **Student** | `str` (e.g. `"S01"`) | Candidate participant with defined skill proficiencies and ranked preferences. |
| **Project** | `str` (e.g. `"P1"`) | Target semester offering with capacity limits and required/desired skills. |
| **Skill** | `str` (e.g. `"python"`) | Competency keyword indexed in catalog. |
| **Run** | `str` (UUIDv4) | Single administrative optimization event. |
| **Solution** | `str` (UUIDv4) | Individual feasible Pareto allocation alternative produced within a run. |
| **Fixed Lock** | `(student_id, project_id)` | Administrative lock that must be satisfied in all generated solutions. |

---

## 3. Data Transfer Objects (DTOs)

### 3.1 `RunRequest`
The structured input submitted by Component A to initiate validation or execution:

```python
@dataclasses.dataclass(frozen=True)
class RunRequest:
    students: list[models.Student]
    projects: list[models.Project]
    skills: list[models.Skill] | None = None
    fixed_assignments: list[models.FixedAssignment] | None = None
    strategy_key: str = "PREFERENCE"
    max_alternatives: int = 3
    notes: str = ""
```

### 3.2 `ValidationOutcome`
Returned by `validate_inputs` before any solver execution:

```python
@dataclasses.dataclass(frozen=True)
class ValidationOutcome:
    is_valid: bool = True
    is_feasible: bool = True
    errors: list[str] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)
    infeasibility_reasons: list[str] = dataclasses.field(default_factory=list)
```

### 3.3 `RunStatus`
Execution lifecycle enum:

```python
class RunStatus(enum.Enum):
    COMPLETED = "COMPLETED"
    INFEASIBLE = "INFEASIBLE"
    INVALID_INPUT = "INVALID_INPUT"
    WARNING = "WARNING"
    FAILED = "FAILED"
```

### 3.4 `RunComparison`
The side-by-side comparison structure returned by `compare_solutions`:

```python
@dataclasses.dataclass(frozen=True)
class RunComparison:
    solution_a_id: str
    solution_a_alt: int
    solution_b_id: str
    solution_b_alt: int
    delta_metrics: dict[str, Any]
    changed_assignments: list[dict[str, Any]]
    changed_students_count: int
    total_students: int
    is_distinct: bool
    rank_improved_count: int
    rank_worsened_count: int
    delta_mean_skill_fit: float
    delta_mean_rank: float
    delta_unranked_count: int
    trade_off_summary: list[str]
```

---

## 4. Contract Operations & Signatures

```python
class AssignmentEngineContract(abc.ABC):
    """Abstract interface defining Component B contract."""

    @abc.abstractmethod
    def validate_inputs(self, request: RunRequest) -> ValidationOutcome:
        """Validates cohort and constraints before attempting optimization."""

    @abc.abstractmethod
    def execute_run(self, request: RunRequest) -> models.AssignmentRun:
        """Executes the assignment algorithm and generates solutions."""

    @abc.abstractmethod
    def list_runs(self, limit: int = 20) -> list[models.AssignmentRun]:
        """Retrieves historical assignment runs."""

    @abc.abstractmethod
    def get_run(self, run_id: str) -> models.AssignmentRun | None:
        """Retrieves a specific run by identifier."""

    @abc.abstractmethod
    def get_solution(self, solution_id: str) -> models.Solution | None:
        """Retrieves a specific solution and its student allocations."""

    @abc.abstractmethod
    def compare_solutions(
        self, solution_a_id: str, solution_b_id: str
    ) -> models.RunComparison:
        """Compares two alternative solutions side-by-side."""
```

---

## 5. Persistence Responsibilities

1. **Relational Database Ownership**:
   - `RunRepository` is encapsulated within Component B for storing `AssignmentRun`, `Solution`, and `Assignment` records.
   - To preserve relational foreign-key integrity in SQLite, `AssignmentEngine.execute_run()` ensures that any in-memory `Student`, `Project`, and `FixedAssignment` records supplied in `RunRequest` are synchronized to their respective tables before committing solution allocations.
2. **Immutable Runs and Solutions**:
   - Assignment runs and their generated alternative solutions are append-only.
   - When inputs or fixed constraints are revised, the system does not mutate previous runs; it executes a new run with a unique run identifier, preserving complete historical auditability.

---

## 6. Integration Usage Example

```python
from app.contract import contract
from app.engine import solvers

# 1. Instantiate engine via interface
engine: contract.AssignmentEngineContract = solvers.AssignmentEngine()

# 2. Formulate RunRequest
request = contract.RunRequest(
    students=cohort_students,
    projects=catalog_projects,
    fixed_assignments=[
        models.FixedAssignment(student_id="S02", project_id="P2", reason="Fellowship")
    ],
    strategy_key="PREFERENCE",
    max_alternatives=3,
)

# 3. Pre-run validation
outcome = engine.validate_inputs(request)
if not outcome.is_valid or not outcome.is_feasible:
    print(f"Validation failed: {outcome.errors} | Infeasibility: {outcome.infeasibility_reasons}")
else:
    # 4. Execute optimization run
    run = engine.execute_run(request)
    print(f"Run {run.id} status: {run.status}, Generated {len(run.solutions)} solutions.")

    # 5. Compare two Pareto alternatives
    if len(run.solutions) >= 2:
        comparison = engine.compare_solutions(run.solutions[0].id, run.solutions[1].id)
        print(f"Shifted students: {comparison.changed_students_count}")
        print(f"Trade-offs: {comparison.trade_off_summary}")
```
