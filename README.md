# TECH5: Student-to-Project Assignment Decision Support System
### Student-to-Project Assignment Decision Support System
**NHH Norwegian School of Economics — Department of Business and Management Science**  
*Course: TECH5 Programming & Application Design*

---

## 1. Project Overview & Starter Kit Structure

Welcome to the **TECH5 Collaborative Project: Student-to-Project Assignment Decision Support System (DSS)**.


This repository contains the completed application developed during a three-week collaborative software engineering project. The application assists academic coordinators and decision-makers in assigning students to semester research and capstone projects under multiple competing criteria:
- **Student ranked preferences** (satisfaction / rank regret)
- **Student technical proficiencies & project skill requirements** (competence matching)
- **Project capacity constraints** (minimum and maximum headcount quotas)
- **Administrative fixed assignments** (pre-allocated student-to-project locks)

In accordance with the course specification (`assignment/projectTech5.tex`), the application avoids microservices, network communication, web APIs, or distributed deployment. It is structured as **two modular, independently testable components** running within a single in-process Python application:

```text
TECH5Project/
├── app/
│   ├── contract/             # Shared in-process Python component contract
│   │   ├── contract.py       # AssignmentEngineContract ABC & strongly typed DTOs
│   │   └── mocks.py          # Complete MockAssignmentEngine for immediate testing
│   ├── domain/               # Shared domain entities & validation rules
│   │   ├── models.py         # Student, Project, Skill, Preference, Run, Solution
│   │   └── validation.py     # Cohort validation & feasibility pre-checks
│   ├── engine/               # Component B: Assignment Engine (Team B Tasks)
│   │   ├── solvers.py        # Optimization engine & strategy skeletons [TODO: Team B]
│   │   └── metrics.py        # Analytical indicators & fairness metrics [TODO: Team B]
│   ├── persistence/          # Shared relational persistence layer
│   │   ├── database.py       # Thread-safe SQLite database manager (WAL mode)
│   │   ├── repositories.py   # Student, Project, Skill, Run repositories
│   │   └── schema.sql        # 3NF relational database schema
│   └── visualization/        # Component A: Visualization & UI (Team A)
│       ├── routes.py         # Flask views, controllers, & engine dispatch
│       ├── templates/        # Jinja2 responsive HTML5 templates
│       └── static/           # CSS stylesheets & client assets
├── assignment/               # Course assignment brief (projectTech5.tex)
├── docs/                     # Deliverable documentation & student templates
│   ├── analytical_note_template.md   # Deliverable 6 template for student report
│   ├── analytical_formulation.md     # Analytical requirements & modeling guide
│   ├── architecture.md               # System architecture & design patterns
│   ├── database_design.md            # ERD, 3NF schema, & analytical SQL queries
│   ├── internal_component_contract.md# Component contract documentation
│   ├── reproducible_demonstration.md # Demonstration walkthrough script
│   ├── team_reflection_and_rubric.md # Collaboration reflection & rubric guide
│   └── testing_and_quality.md        # Test matrix & edge case documentation
├── tests/                    # Automated test suite (46 pytest tests)
├── requirements.txt          # Python dependencies
└── run.py                    # Application launch entry point
```

---

## 2. Team Division & Responsibilities

The project is designed for two collaborating student development teams:

### Team A: Visualization and Recommendation Component (`app/visualization/`)
- **Workflow & UI**: Complete web interface for inspecting cohorts, editing student/project/skill data, creating fixed assignments, and triggering assignment runs.

- **Assignment Engine Integration**: The web application uses the real `AssignmentEngine` implemented in `app/engine/solvers.py` to generate student-to-project assignments. The `MockAssignmentEngine` (`app/contract/mocks.py`) is retained for automated testing and contract verification.

- **Comparison & Recommendations**: Side-by-side comparison of alternative solutions, student re-allocation diffs, and transparent recommendations across multiple administrative priorities.

### Team B: Assignment Engine (`app/engine/`)
- **Optimization Formulation (`app/engine/solvers.py`)**:
  - Implement Integer Linear Programming (ILP) using Pyomo with the HiGHS solver (`app/engine/solvers.py`).
  - Implement concrete strategies inheriting from `AssignmentStrategy` (`PreferenceOrientedSolver`, `SkillFitOrientedSolver`, `BalancedTradeoffSolver`).
  - Implement generation of distinct Pareto alternatives via no-good integer cuts.
  - Implement `AssignmentEngine.run_assignment(...)` and `AssignmentEngine.execute_run(...)`.
- **Analytical Indicators (`app/engine/metrics.py`)**:
  - Implement `calculate_skill_fit(...)` (normalized skill-fit score $\sigma_{s,p}$).
  - Implement `calculate_gini(...)` (Gini coefficient of preference ranks $G$).
  - Implement `calculate_solution_indicators(...)` (feasibility, efficiency, fairness, capacity utilization).
  - Implement `compare_solutions(...)` (comparative indicator deltas and changed student allocations).
- **Analytical Note**: Complete the formal mathematical report using [`docs/analytical_note_template.md`](docs/analytical_note_template.md).

---

## 3. Quickstart & Installation

### 3.1 Prerequisites
- Python 3.10+ (tested up to Python 3.14)
- Git

### 3.2 Setup Virtual Environment
```powershell
# 1. Clone repository & enter workspace
git clone <repository-url>
cd TECH5Project

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows PowerShell
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the application
python run.py
```

Navigate to **`http://127.0.0.1:5000`** in your browser.


> [!TIP]
> **Assignment Engine:** The web application uses the real optimization engine in `app/engine/solvers.py`, implemented with Pyomo and HiGHS. The `MockAssignmentEngine` is retained for automated testing and is not used during normal application operation.


---

## 4. Automated Testing & Verification


The repository contains **75 automated tests** covering component functionality, database persistence, integration, input validation, optimization, and edge cases:


```powershell
# Run the complete test suite
.\.venv\Scripts\pytest -v
```


### Current Test Results

The complete test suite has been verified using Python 3.10.4 and pytest 9.1.1.

- **75 tests passed**
- **0 tests failed**
- **0 expected failures (XFAIL)**

The automated tests cover:

- **Component tests:** Domain models, input validation, optimization strategies, analytical metrics, and user interface functionality.
- **Database tests:** Database initialization, persistence, and retrieval of project, student, and assignment data.
- **Integration tests:** Contract compliance, complete assignment workflows, and infeasible scenarios.
- **Edge-case tests:** All 15 boundary conditions documented in `docs/analytical_note.md`.

For detailed test descriptions and the complete execution log, see [`docs/testing_and_quality.md`](docs/testing_and_quality.md).


---


