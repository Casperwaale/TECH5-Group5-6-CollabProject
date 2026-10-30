# Deliverable 3: System Architecture Specification & Design Rationale

## 1. Executive Architectural Overview

The **TECH5 Student-to-Project Assignment Decision Support System (DSS)** assigns a cohort of students to semester projects at NHH. An allocation must respect **project capacity bounds**, **mandatory skill requirements** and **administrative locks**, while trading off **student ranked preferences** against **skill fit**. The system computes several distinct alternatives, measures each one, and leaves the final choice to the coordinator.

The system is one Python application with **two components** that only meet at an internal contract:

1. **Component A (Visualization & Recommendation, Team A, `app/visualization/`)**:
   - User workflow, data entry (CRUD), demonstration scenarios, role switching (Administrator, Coordinator, Student Viewer), the run trigger, side-by-side comparison of two alternatives, and the recommendations page.
2. **Component B (Assignment Engine, Team B, `app/engine/` and `app/domain/validation.py`)**:
   - Validates the input, solves an **integer linear programme (ILP)** built in **Pyomo** and solved with **HiGHS** (`appsi_highs`, one thread), generates **distinct alternatives** with integer no-good cuts, computes the evaluation indicators, and saves each run with its diagnostics.

The contract (`app/contract/contract.py`) and the domain objects (`app/domain/models.py`) are shared by both teams, and so is the SQLite persistence layer (`app/persistence/`). The mathematical model itself is documented in `docs/analytical_note.md` §2 and `docs/model/ilp_formulation.tex`.

---

## 2. Component Diagram & Internal Interface

```mermaid
flowchart TD
    subgraph Component_A["Component A: Visualization & Recommendation (app/visualization)"]
        UI["Jinja2 templates + CSS"]
        WebRoutes["Flask blueprint: routes.py"]
        RoleAuth["Role checks: auth.py (Admin / Coordinator / Student)"]
    end

    subgraph InternalContract["Internal Component Contract (app/contract)"]
        ContractABC["AssignmentEngineContract (ABC)"]
        DTOs["RunRequest | ValidationOutcome | DiagnosticInfo | RunStatus"]
        Mock["MockAssignmentEngine (mocks.py)"]
    end

    subgraph Component_B["Component B: Assignment Engine (app/engine, app/domain/validation.py)"]
        SolverEngine["AssignmentEngine (implements the contract)"]
        ValidationEngine["validation.validate_cohort"]
        StrategyPattern["Strategy pattern: Preference, SkillFit, Balanced"]
        ILP["Pyomo ILP + HiGHS, no-good cuts"]
        MetricsEngine["metrics.py: indicators and comparison"]
        RecEngine["recommendations.py: one advice per policy priority"]
    end

    subgraph Shared["Shared domain and persistence"]
        Models["Domain dataclasses (app/domain/models.py)"]
        Repos["Repositories (app/persistence/repositories.py)"]
        DBMgr["DatabaseManager (SQLite, foreign keys on, WAL)"]
        Schema["schema.sql"]
    end

    UI --> WebRoutes
    WebRoutes --> RoleAuth
    WebRoutes -->|"validate_inputs, execute_run, compare_solutions"| ContractABC
    ContractABC -.->|implemented by| SolverEngine
    ContractABC -.->|implemented by| Mock
    WebRoutes -->|"generate_recommendations(run.solutions)"| RecEngine

    SolverEngine --> ValidationEngine
    SolverEngine --> StrategyPattern
    StrategyPattern --> ILP
    SolverEngine --> MetricsEngine

    WebRoutes -->|"CRUD, list runs"| Repos
    SolverEngine -->|"save_run"| Repos
    Repos --> DBMgr
    DBMgr --> Schema

    ContractABC --- Models
    Repos --- Models
```

**One optimization run, step by step.** The route builds a `RunRequest` from the stored cohort and calls `AssignmentEngine.execute_run`:

1. **Validate** (`validation.validate_cohort`). Invalid input is saved as `INVALID_INPUT`; input that is provably impossible (for example fewer seats than students) is saved as `INFEASIBLE`. Invalid is reported before infeasible (R10, D16).
2. **Solve.** Alternative 1 uses the strategy the user selected; each next alternative uses the next strategy in turn (R15) and adds a no-good cut for every earlier alternative (R5). The loop stops early when the cuts make the model infeasible.
3. **Measure.** `metrics.compute_solution_indicators` scores every alternative with the same function (feasibility, efficiency, fairness, capacity).
4. **Save.** The run, its solutions and assignments are saved through `RunRepository.save_run` with status `COMPLETED`, `INFEASIBLE` or `FAILED`, and the route redirects to the run page.

The comparison page calls `compare_solutions` (which uses `metrics.compare_two_solutions`), and the recommendations page calls `recommendations.generate_recommendations` on the solutions of one run.

---

## 3. Design Rationale: Two-Component Modular Monolith vs. Microservices

### 3.1 Motivation for In-Process Two-Component Architecture
1. **Curricular Alignment & Feasibility**:
   - The primary pedagogical objective is object-oriented software design, relational database integration, and decision support. Microservices introduce substantial operational complexity (distributed networking, ports, HTTP status translation, retries, serialization boilerplate) that distracts from the core analytical problem.
2. **High Modularity Without Operational Overhead**:
   - Component A and Component B maintain strict separation of concerns. Component B has zero knowledge of Flask request objects, HTML templates, or cookies. It can be instantiated, validated, and tested headlessly in pure Python scripts or test harnesses (`docs/reproducible_demonstration.md` §2.6).
3. **Type Safety**:
   - In-process contract calls pass typed dataclasses (`RunRequest`, `ValidationOutcome`, `AssignmentRun`, `RunComparison`) directly, so there is no JSON schema that can drift between the components.
4. **Performance**:
   - Direct method calls avoid serialization and network latency. Each strategy solves a 300-student cohort in under 0.4 s (`docs/analytical_note.md` §1.2), so the user can wait for the result in the browser.

### 3.2 Decisions Specific to This Implementation
1. **The contract is the only dependency on the engine's internals.** Component A types its engine as `AssignmentEngineContract` and calls only its methods for running and comparing. `MockAssignmentEngine` implements the same contract with synthetic numbers, so Team A could build every page before the real engine existed; the routes fall back to the mock only if the engine raises `NotImplementedError`. Two direct dependencies remain by design: the routes call `generate_recommendations`, which reads nothing but `Solution.indicators`, and the repositories for data entry and for reading saved runs. Both depend on stable keys and tables (R11), not on solver code.
2. **ILP with Pyomo and HiGHS (D1, approved as Q1).** Team B learned this toolchain in TECH4, so every line of the model can be explained by the team. ILP keeps hard constraints exact (R2), proves when no further distinct alternative exists (R5), and makes each strategy an explicit objective function. The reasoning is set out in `docs/analytical_note.md` §1.2.
3. **One model, three objectives.** The sets, parameters and constraints are built once in `prepare_data` and `build_model`; a strategy only supplies the objective coefficient of each `x[s,p]` and the sense (§4.1, D14). A constraint fix therefore applies to all three strategies at once, and the strategies differ only where they should.
4. **Validation before solving.** Clear errors are caught in plain Python with readable messages, before Pyomo is called. The solver only has to prove the harder, combined conflicts infeasible. No constraint is ever relaxed to produce an answer (R2).
5. **Deterministic results (R16).** Sets are built in sorted identifier order and HiGHS runs on one thread, so the same input gives the same alternatives with the same Pyomo and HiGHS versions. The demonstration guide relies on this.

---

## 4. Object-Oriented Architecture & Design Patterns

### 4.1 Strategy Pattern (Assignment Algorithms)
The Assignment Engine defines an abstract base strategy `AssignmentStrategy(abc.ABC)` with three concrete subclasses. All three solve the same model (`analytical_note.md` §2.4); they differ in the objective:
- `PreferenceOrientedSolver`: minimises the total preference rank (unranked projects count as rank $m + 1$, R14), with a small skill-fit tie-break.
- `SkillFitOrientedSolver`: maximises the total skill fit over the non-mandatory requirements (R4), with a small preference tie-break.
- `BalancedTradeoffSolver`: solves in two stages. Stage 1 minimises the worst assigned rank; stage 2 keeps that worst rank and maximises an equal mix ($\lambda = 0.5$) of preference score and skill fit. It is the only strategy that overrides `solve`.

`calculate_cost_or_utility(data, s, p)` is the abstract method each subclass implements; `solve` builds the shared model, adds the objective from these coefficients and any no-good cuts, and calls HiGHS.

```
       +--------------------------------------------+
       |          AssignmentStrategy (ABC)          |
       +--------------------------------------------+
       | + sense                                    |
       | + calculate_cost_or_utility(data, s, p)  * |
       | + solve(students, projects, fixed, cuts)   |
       +--------------------------------------------+
             ^                  ^               ^
             |                  |               |
  +----------+------+   +-------+--------+   +--+--------------------+
  | Preference      |   | SkillFit       |   | BalancedTradeoff      |
  | OrientedSolver  |   | OrientedSolver |   | Solver                |
  | sense = min     |   | sense = max    |   | overrides solve():    |
  |                 |   |                |   | stage 1 min-max rank, |
  |                 |   |                |   | stage 2 balance       |
  +-----------------+   +----------------+   +-----------------------+
```

### 4.2 Abstract Contract Pattern (Component Boundary)
`AssignmentEngineContract` defines the public interface required by Component A: `validate_inputs`, `execute_run`, `list_runs`, `get_run`, `get_solution` and `compare_solutions`. `AssignmentEngine` implements all of them, and `MockAssignmentEngine` implements the same interface with synthetic data, so either can be substituted without touching Component A.

### 4.3 Repository Pattern (Data Access Layer)
Persistence operations are encapsulated into domain repositories:
- `StudentRepository`: Manages `students`, `student_skills`, and `preferences`.
- `ProjectRepository`: Manages `projects` and `project_requirements`.
- `SkillRepository`: Manages defined competencies.
- `FixedAssignmentRepository`: Manages administrative pre-allocation locks.
- `RunRepository`: Manages `assignment_runs`, `solutions`, and `assignments`.

All repositories share one `DatabaseManager`, which turns on foreign-key enforcement for every connection, so an assignment can only refer to a project that exists.

### 4.4 Class Diagram: Contract, Engine and Persistence

```mermaid
classDiagram
    direction TB

    class AssignmentEngineContract {
        <<abstract>>
        +validate_inputs(request) ValidationOutcome
        +execute_run(request) AssignmentRun
        +list_runs(limit) list~AssignmentRun~
        +get_run(run_id) AssignmentRun
        +get_solution(solution_id) Solution
        +compare_solutions(a_id, b_id) RunComparison
    }
    class AssignmentEngine {
        +run_repo: RunRepository
        +strategies: dict~str, AssignmentStrategy~
        -_save_entities(request)
    }
    class MockAssignmentEngine
    class RunRequest {
        <<dataclass>>
        +students: list~Student~
        +projects: list~Project~
        +skills: list~Skill~
        +fixed_assignments: list~FixedAssignment~
        +strategy_key: str
        +max_alternatives: int
    }
    class ValidationOutcome {
        <<dataclass>>
        +is_valid: bool
        +is_feasible: bool
        +errors: list~str~
        +warnings: list~str~
        +infeasibility_reasons: list~str~
    }
    class RunStatus {
        <<enumeration>>
        COMPLETED
        INFEASIBLE
        INVALID_INPUT
        WARNING
        FAILED
    }

    class AssignmentStrategy {
        <<abstract>>
        +name: str
        +description: str
        +sense
        +calculate_cost_or_utility(data, s, p) float*
        +solve(students, projects, fixed_assignments, excluded_solutions) tuple
    }
    class PreferenceOrientedSolver
    class SkillFitOrientedSolver
    class BalancedTradeoffSolver {
        +solve(...) tuple
    }

    class RunRepository {
        +save_run(run)
        +list_runs(limit)
        +get_run(run_id)
        +get_solution(solution_id)
    }
    class StudentRepository
    class ProjectRepository
    class SkillRepository
    class FixedAssignmentRepository
    class DatabaseManager {
        +db_path
        +connection()
        +initialize_schema()
    }

    AssignmentEngineContract <|-- AssignmentEngine
    AssignmentEngineContract <|-- MockAssignmentEngine
    AssignmentEngineContract ..> RunRequest : uses
    AssignmentEngineContract ..> ValidationOutcome : returns
    AssignmentEngine ..> RunStatus : sets
    AssignmentEngine *-- "3" AssignmentStrategy : strategies
    AssignmentStrategy <|-- PreferenceOrientedSolver
    AssignmentStrategy <|-- SkillFitOrientedSolver
    AssignmentStrategy <|-- BalancedTradeoffSolver
    AssignmentEngine o-- RunRepository : run_repo
    AssignmentEngine ..> StudentRepository : saves cohort
    AssignmentEngine ..> ProjectRepository : saves cohort
    AssignmentEngine ..> SkillRepository : saves cohort
    AssignmentEngine ..> FixedAssignmentRepository : saves cohort
    RunRepository --> DatabaseManager
    StudentRepository --> DatabaseManager
    ProjectRepository --> DatabaseManager
    SkillRepository --> DatabaseManager
    FixedAssignmentRepository --> DatabaseManager
```

The module-level functions are not classes and so are not drawn: `validation.validate_cohort` (returns a `ValidationResult`, which the engine copies into a `ValidationOutcome`), the model functions `prepare_data`, `build_model`, `solve_model` and `read_assignments` in `solvers.py`, `metrics.compute_solution_indicators` and `metrics.compare_two_solutions`, and `recommendations.generate_recommendations` (returns `RecommendationItem` objects).

### 4.5 Class Diagram: Domain Model

```mermaid
classDiagram
    direction LR

    class Skill {
        +id: str
        +name: str
        +description: str
    }
    class Student {
        +id: str
        +display_name: str
        +skills: dict~str, int~
        +preferences: list~Preference~
        +get_preference_rank(project_id) int
        +get_skill_level(skill_id) int
    }
    class Preference {
        +student_id: str
        +project_id: str
        +rank: int
    }
    class Project {
        +id: str
        +title: str
        +description: str
        +min_capacity: int
        +max_capacity: int
        +requirements: list~ProjectRequirement~
    }
    class ProjectRequirement {
        +project_id: str
        +skill_id: str
        +minimum_level: int
        +is_mandatory: bool
    }
    class FixedAssignment {
        +student_id: str
        +project_id: str
        +status: str
        +reason: str
    }
    class AssignmentRun {
        +id: str
        +created_at: str
        +status: str
        +configuration: dict
        +solutions: list~Solution~
        +diagnostics: dict
    }
    class Solution {
        +id: str
        +run_id: str
        +alternative_number: int
        +strategy_name: str
        +objective_value: float
        +assignments: list~Assignment~
        +indicators: dict
        +get_assignment_for_student(student_id) Assignment
    }
    class Assignment {
        +student_id: str
        +project_id: str
        +is_fixed: bool
        +preference_rank: int
        +skill_fit_score: float
        +unmet_requirements: list~str~
    }
    class RunComparison {
        +solution_a_id: str
        +solution_b_id: str
        +delta_metrics: dict
        +changed_assignments: list
        +trade_off_summary: list~str~
    }

    Student "1" *-- "0..*" Preference
    Preference "0..*" --> "1" Project : ranks
    Student ..> Skill : skills keyed by id, level 1-5
    Project "1" *-- "0..*" ProjectRequirement
    ProjectRequirement "0..*" --> "1" Skill
    FixedAssignment "0..1" --> "1" Student : locks
    FixedAssignment "0..*" --> "1" Project : to
    AssignmentRun "1" *-- "0..*" Solution : alternatives
    Solution "1" *-- "0..*" Assignment
    Assignment "0..*" --> "1" Student
    Assignment "0..*" --> "1" Project
    RunComparison ..> Solution : compares two
```

All domain objects are dataclasses with `to_dict` and `from_dict`. The diagram mirrors the relational schema in §5: compositions here are the one-to-many tables there, and a student's skills are stored as `student_skills` rows (`StudentSkill`), but held in memory as a dictionary from skill ID to level.

---

## 5. Relational Database Architecture

```mermaid
erDiagram
    students ||--o{ student_skills : "possesses"
    skills ||--o{ student_skills : "classified under"
    students ||--o{ preferences : "submits"
    projects ||--o{ preferences : "ranked in"
    projects ||--o{ project_requirements : "demands"
    skills ||--o{ project_requirements : "specified by"
    students ||--o{ fixed_assignments : "locked to"
    projects ||--o{ fixed_assignments : "hosts"
    assignment_runs ||--o{ solutions : "produces"
    solutions ||--o{ assignments : "allocates"
    students ||--o{ assignments : "assigned"
    projects ||--o{ assignments : "contains"

    students {
        TEXT id PK
        TEXT display_name
    }
    projects {
        TEXT id PK
        TEXT title
        TEXT description
        INTEGER min_capacity
        INTEGER max_capacity
    }
    skills {
        TEXT id PK
        TEXT name
        TEXT description
    }
    student_skills {
        TEXT student_id PK,FK
        TEXT skill_id PK,FK
        INTEGER level
    }
    project_requirements {
        TEXT project_id PK,FK
        TEXT skill_id PK,FK
        INTEGER minimum_level
        INTEGER is_mandatory
    }
    preferences {
        TEXT student_id PK,FK
        TEXT project_id PK,FK
        INTEGER rank
    }
    fixed_assignments {
        TEXT student_id PK,FK
        TEXT project_id FK
        TEXT status
        TEXT reason
    }
    assignment_runs {
        TEXT id PK
        TEXT created_at
        TEXT status
        TEXT configuration
        TEXT diagnostics
    }
    solutions {
        TEXT id PK
        TEXT run_id FK
        INTEGER alternative_number
        TEXT strategy_name
        REAL objective_value
        TEXT indicators
        TEXT warnings
        TEXT diagnostics
    }
    assignments {
        INTEGER id PK
        TEXT solution_id FK
        TEXT student_id FK
        TEXT project_id FK
        INTEGER is_fixed
        INTEGER preference_rank
        REAL skill_fit_score
        TEXT unmet_requirements
    }
```

---

## 6. Role-Based Access Control (RBAC)

The application models three explicit business roles in `app/visualization/auth.py`:
1. **Course Administrator (`ADMIN`)**: Full authorization. Can edit students, projects, skills, and fixed assignments, trigger optimization runs, and switch active roles.
2. **Program Coordinator (`COORDINATOR`)**: Operational authorization. Can manage fixed assignment locks, trigger solver runs, and inspect detailed recommendations and comparisons. Read-only on baseline student data.
3. **Student Viewer (`STUDENT`)**: Transparency view. Can browse anonymized dashboard metrics, project descriptions, and high-level allocation summaries. Mutating actions are disabled.
