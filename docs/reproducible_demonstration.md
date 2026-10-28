# TECH5 Assignment Support System: Reproducible Demonstration Walkthrough

## 1. Demonstration Overview

This guide provides instructors, evaluators, and students with an exact, reproducible walkthrough of the **Student-to-Project Assignment Decision Support System**. It exercises all core functional capabilities across the four benchmark cohorts pre-configured in the platform: data entry, run trigger, distinct alternatives, comparison, recommendations, fixed assignments and infeasibility handling.

All numbers below come from the real assignment engine (ILP, `app/engine/solvers.py`) and indicators (`app/engine/metrics.py`). The engine is deterministic (R16 in `docs/team_b_decisions.md`): the same cohort always gives the same alternatives, so every value in this guide can be reproduced exactly.

### Quick Start
1. Activate the virtual environment and install the dependencies (once):
   ```bash
   source .venv/bin/activate          # macOS/Linux
   .venv\Scripts\Activate.ps1         # Windows (PowerShell)
   pip install -r requirements.txt
   ```
2. Start the integrated application:
   ```bash
   python run.py                      # http://127.0.0.1:5000
   python run.py 5001                 # macOS: port 5000 is taken by AirPlay Receiver
   ```
3. Open the address in a browser. The role switcher in the top bar must be **Administrator** (the default) or **Programme Coordinator** to load scenarios and launch runs.
4. Optional: run the automated test suite with `pytest -v`. Expected result: all tests pass, with no failures and no expected failures.

---

## 2. Scenario 1: Standard Cohort (Trade-Off Benchmark)

### 2.1 Scenario Objective
Demonstrates distinct alternatives generated with no-good integer cuts, one per strategy, and the trade-off between student preference satisfaction and project skill fit.

### 2.2 Cohort Composition
- **Students**: 10 students (`S01` to `S10`) with complementary competencies across Python, SQL, Machine Learning, Web Dev, and FinTech.
- **Projects**: 4 projects (`P1`: Sustainable FinTech Risk Engine, `P2`: Cloud Data Pipeline & Lakehouse, `P3`: Healthcare Predictive ML Assistant, `P4`: Smart City Mobility Portal) with capacity bounds $[1, 3]$ each (Total Capacity = 12 $\ge 10$ students).
- **Constraints**: No fixed pre-allocations.

### 2.3 Step-by-Step Execution (Web Interface)
1. In the top navigation, click **Scenarios**.
2. Under **1. Standard Trade-Off Benchmark**, click **"Load Standard Benchmark →"**.
3. You return to the Dashboard with a success message, and the KPI cards show **Student Cohort 10**, **Active Projects 4**, **Total Max Capacity 12 ✓ Sufficient Capacity** and **Fixed Locks 0**.
4. In the **Optimization Run Trigger Panel**:
   - Strategy: `Student Preference Maximization (Minimize Rank Regret)`
   - Distinct Alternatives: `3 Distinct Solutions`
   - Click **"Launch Optimization Run"**.
5. You are redirected to `/runs/{run_id}`. The diagnostics read *"Found 3 distinct alternative(s) of 3 requested."* The alternatives use the strategies in turn, starting with the one selected (R15):

| Alternative | Strategy | Avg skill fit | Avg pref. rank | Worst rank | Rank Gini | Preference distribution |
|---|---|---|---|---|---|---|
| #1 | PREFERENCE | 98.3% | 1.0 | 1 | 0.0 | rank_1: 10 |
| #2 | SKILL_FIT | 100.0% | 1.1 | 2 | 0.0818 | rank_1: 9, rank_2: 1 |
| #3 | BALANCED | 98.3% | 1.1 | 2 | 0.0818 | rank_1: 9, rank_2: 1 |

   - Alternative 1 gives every student their first choice.
   - Alternative 2 moves one student (`S06`, Fredrik Berg) from `P3` to their second choice `P2`, which raises mean skill fit to 100%.
   - Alternative 3 moves a different student (`S01`, Alice Chen) from `P3` to their second choice `P2`. Because of the no-good cuts, each alternative differs from every earlier one in at least one student's project (R5).

### 2.4 Side-by-Side Solution Comparison
1. In the top navigation, click **Compare**. With no selection, the page compares the first two alternatives of the latest run.
2. To choose other solutions, select:
   - Solution A: `Alt #1 – PREFERENCE (Run: …)`
   - Solution B: `Alt #2 – SKILL_FIT (Run: …)`
   - Click **"Compare Allocations →"**.
3. The comparison page shows (all deltas are B minus A):
   - **Delta cards**: Changed Student Allocations `1`, Δ Average Skill Fit `+1.7%`, Δ Average Preference Rank `+0.1`, Rank Shifts `0 ↑ / 1 ↓`, Δ Rank Gini `+0.0818`.
   - **Trade-off Findings**: plain-language sentences, e.g. *"Mean skill fit increases by 0.0167 in Solution B."*
   - **Detailed Allocation Shifts**: Fredrik Berg moves from Healthcare Predictive ML Assistant (Choice #1) to Cloud Data Pipeline & Lakehouse (Choice #2), shown as `▼ 1 rank worse`.

### 2.5 Inspecting Decision-Support Recommendations
1. On the run page, click **"View Recommendations →"** (route `/recommendations/{run_id}`).
2. The **Transparent Decision Recommendations** page presents one recommendation per policy priority:
   - **Student Preference Maximization** → Alternative #1 (lowest average rank, nobody outside their preferences, worst rank 1).
   - **Project Skill Quality & Delivery Assurance** → Alternative #2 (highest mean skill fit).
   - **Balanced & Egalitarian Allocation** → Alternative #1 (lowest rank Gini, 0.0, then lowest rank variance and mean rank).
3. Each recommendation separates the **criteria evaluated**, the **calculated evidence** and the **policy advice**, and the page states that the final decision rests with the programme committee.

### 2.6 Headless In-Process Contract Execution (Python)
The Assignment Engine can be invoked directly in Python without starting the web server, demonstrating contract independence. Run this from the repository root with the virtual environment active:
```python
from app import create_app
from app.contract import contract
from app.engine import solvers
from app.samples import demo_data

create_app()  # initialises the SQLite database the engine saves runs to

cohort = demo_data.get_standard_scenario()
request = contract.RunRequest(
    students=cohort["students"],
    projects=cohort["projects"],
    skills=cohort["skills"],
    strategy_key="PREFERENCE",
    max_alternatives=3,
)

# Execute optimization via the internal contract
run = solvers.AssignmentEngine().execute_run(request)
print(f"Status: {run.status}")
print(f"Solutions generated: {len(run.solutions)}")
for sol in run.solutions:
    print(f"Alt {sol.alternative_number} ({sol.strategy_name}): "
          f"Mean Rank={sol.indicators['fairness']['mean_rank']}, "
          f"Mean Skill Fit={sol.indicators['efficiency']['mean_skill_fit']:.2f}")
```
Expected output:
```
Status: COMPLETED
Solutions generated: 3
Alt 1 (PREFERENCE): Mean Rank=1.0, Mean Skill Fit=0.98
Alt 2 (SKILL_FIT): Mean Rank=1.1, Mean Skill Fit=1.00
Alt 3 (BALANCED): Mean Rank=1.1, Mean Skill Fit=0.98
```

---

## 3. Scenario 2: Fixed Assignment & Ripple Effect Analysis

### 3.1 Scenario Objective
Demonstrates administrative pre-allocation locks ($x_{s^*, p^*} = 1$), strict constraint preservation in every alternative, and interactive lock-and-rerun.

### 3.2 Cohort Composition
- Base standard cohort with student **`S02` (Bob Smith)** locked to project **`P2` (Cloud Data Pipeline & Lakehouse)** under an approved research grant, although `P2` is only the third choice on Bob's list (`P1`, `P4`, `P2`).

### 3.3 Step-by-Step Execution
1. Navigate to **Scenarios** and click **"Load Fixed Assignment Scenario →"** under **2. Fixed Assignment & Rerun Scenario**. The Dashboard shows **Fixed Locks 1**.
2. In the top navigation, click **Fixed Locks**.
   - `S02` $\to$ `P2` is listed with status `APPROVED` and its justification.
3. Return to **Dashboard** and click **"Launch Optimization Run"** (Preference strategy, 3 alternatives).
4. Inspect the generated solutions:
   - In every alternative, `S02` is assigned to `P2` with the **🔒 FIXED LOCK** badge, at rank 3.
   - The lock costs the cohort: Alternative #1 has average preference rank `1.2`, worst rank `3` and rank Gini `0.15` (against 1.0, 1 and 0.0 without the lock). Every other student still gets their first choice in Alternative #1; the cost falls on Bob.
   - Alternatives #2 and #3 (average rank `1.3`, Gini `0.1923`) each move one more student to a lower choice; S08 in Alternative #3 is moved to `P2`.
5. Open any solution with **"Explore Allocations →"**. Each unlocked row has a **"🔒 Lock & Rerun"** button that locks that student to the project they have in this solution and runs the optimization again. For example, lock `S01` to `P3`: a new run starts, and in all three alternatives both `S01 → P3` and `S02 → P2` carry the fixed badge.

---

## 4. Scenario 3: Capacity Deficit (Mathematical Infeasibility)

### 4.1 Scenario Objective
Validates that the system detects structural infeasibility when total project capacity is strictly less than cohort size ($\sum u_p < |S|$), reports it before calling the solver, and never relaxes a constraint to produce an answer.

### 4.2 Cohort Composition
- **Students**: 10 students.
- **Projects**: Capacities reduced to 2, 2, 1, 1 (Total Capacity = 6 seats for 10 students).

### 4.3 Step-by-Step Execution
1. Navigate to **Scenarios** and click **"Load Infeasible Capacity Scenario →"** under **3. Capacity Deficit (Infeasible Case)**.
2. On the Dashboard KPI cards:
   - Student Cohort: `10`
   - Total Max Capacity: `6` with the warning `⚠ Capacity Deficit`
3. Click **"Launch Optimization Run"**.
4. The run is saved and shown with:
   - Run Status: `INFEASIBLE`
   - Diagnostics:
     ```
     The input cannot satisfy every hard constraint.
     Insufficient overall capacity: total cohort size (10) exceeds aggregate maximum project capacity (6).
     ```
   - *"No feasible solutions were generated for this run."* No allocation is created. To resolve it, the coordinator increases project capacities or adds projects; the engine never leaves students unassigned (R1).

---

## 5. Scenario 4: Contradictory Fixed Constraints

### 5.1 Scenario Objective
Verifies that the system rejects an administrator's locks when more students are locked to a project than its maximum capacity ($|F_p| > u_p$).

### 5.2 Cohort Composition
- Project `P1` has a maximum capacity of 3 students.
- 4 students (`S01`, `S02`, `S05`, `S08`) are locked to `P1`.

### 5.3 Step-by-Step Execution
1. Navigate to **Scenarios** and click **"Load Contradictory Scenario →"** under **4. Contradictory Constraints (Validation Error)**. The Dashboard shows **Fixed Locks 4**.
2. Click **"Launch Optimization Run"**.
3. The run is saved with status `INFEASIBLE` and the diagnostics:
   ```
   The input cannot satisfy every hard constraint.
   Fixed assignments (4) for project 'P1' exceed its maximum capacity (3).
   ```
4. No solution is created. The coordinator removes one of the locks under **Fixed Locks** and runs again.

---

## 6. Data Entry (Optional)

Beyond the scenarios, the cohort can be built or edited by hand: **Skills** (create and delete skills), **Projects** (create, edit and delete projects with capacities and skill requirements, marking requirements as mandatory), **Students** (skills and ranked preferences) and **Fixed Locks**. Invalid input is rejected with a message on the page, and an optimization run on hand-entered data follows the same steps as Scenario 1. **Scenarios → Database Reset → Clear All Database Records** clears all cohort data.
