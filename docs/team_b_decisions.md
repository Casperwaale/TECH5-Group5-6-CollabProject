# Team B decisions

The single record of modelling and policy rules for the assignment engine. Agents and team members read this before engine work.

The file has three parts:

1. **Requirements (R):** fixed by the challenge brief or the supplied tests. Not up to us; implement them as written.
2. **Questions for the instructor:** the brief leaves them open, but they are not ours to settle.
3. **Decisions (D):** genuine choices for Team B. When one is made, change its status to **DECIDED**, write the decision and who approved it, and add a line to the log at the bottom.

Status values for decisions: **OPEN** (not decided) · **PROPOSED** (team's choice, awaiting approval) · **DECIDED**

Decision IDs are kept stable; gaps (D3, D5, D6, D9) are items that turned out to be requirements.

---

## 1. Requirements from the brief and tests

### R1. One project per student, unassigned allowed only when capacity is short (was D3)
- "A student should receive at most one project, or exactly one where total project capacity makes this possible." (brief §4)
- Exact allocation when total maximum capacity ≥ number of students. Otherwise every student gets at most one project, and the run is an explicitly allowed partial result.
- Unassigned students are not stored as `Assignment` rows (foreign key to `projects`); they are reported in diagnostics. How the UI shows them is D13.
- Edge case 7 tests `validate_cohort` with exact allocation enforced and must keep rejecting.

### R2. Hard constraints are never relaxed (was D5)
- Hard constraints: capacity limits, mandatory skills, valid identifiers, one project per student, fixed assignments. (brief §5.1)
- If they cannot all hold, for example a fixed assignment that blocks a mandatory skill, the result is **infeasible with diagnostics** naming the conflict. "Do not hide the problem or silently change the constraints." (brief §5.1)

### R3. Fixed assignments are always preserved (was D6)
- The application must "preserve administrative fixed assignments". (brief §2, §5.1)
- All statuses offered by the UI (`APPROVED`, `MANDATORY`, `CONDITIONAL`) are hard locks. The status records why a student is locked; it does not change the constraint.

### R4. Skill fit uses non-mandatory requirements (was D9)
- "Mandatory requirements act as hard constraints, while non-mandatory requirements contribute to skill-fit assessment." (brief §4)
- Score per student–project pair: mean over the project's non-mandatory requirements of `min(1, level / minimum_level)`. No such requirements gives 1.0; a student with no skills gives 0.0. (`tests/test_metrics.py`)
- `unmet_requirements` lists every requirement below the required level.

### R5. Distinct alternatives (was the definition part of D10)
- Up to K distinct feasible solutions, default K = 3. Two solutions differ only when at least one student's project changes. (brief §6)
- If fewer distinct solutions exist, report that honestly; never duplicate one. (brief §6, edge cases 14 and 15)
- With ILP this is a no-good cut against every earlier solution. Do not require more than one student to move.

### R6. Incomplete preferences are allowed, with a warning (was a D11 row)
- The brief says students rank at least three projects (§4), but edge case 1 requires a student with a single ranking to get a solution.
- So fewer than three rankings is a **warning**, not a rejection.

### R7. Skill levels are 1–5 (was a D11 row)
- "Project skill requirements use proficiency levels from 1 to 5." (brief §4)
- A level outside 1–5 is invalid input and is **rejected**.

### R8. The supplied test suite must pass (was D4)
- "The supplied automated test suite must pass without unexpected failures or regressions." (brief §10.3)
- Three tests assert the unimplemented stubs: `test_assignment_engine_initialization`, `test_assignment_engine_raises_not_implemented`, and the `NotImplementedError` checks in `tests/test_contract_and_engine.py`. When the engine replaces the stubs, update each one to check the real behaviour instead (for example, three strategies instead of zero), and say so in the pull request. This entry is the approval AGENTS.md rule 2 refers to.

---

## 2. Questions for the instructor

### Q1. Approval of the assignment method (part of D1)
The brief requires instructor approval before the method becomes the baseline (§7). Send the D1 proposal once Team B agrees on it.
- **Approved by / date:**

### Q2. Mandatory skills: per student or per project? (was D2)
The brief says mandatory requirements are hard constraints (§4) but not whom they apply to.
- **Per student:** every student assigned to the project must meet the level. Ineligible pairs are simply excluded.
- **Per project:** at least one assigned student must meet the level.
- **Hints:** the brief says popular preferences "may leave another project without appropriate skills" (§4), and `docs/analytical_note_template.md` says "satisfied by at least one assigned student"; both lean per project.
- **Answer:**

---

## 3. Team B decisions

### D1. Assignment method and library — OPEN
- **Proposal:** integer linear programming (ILP). One binary variable per eligible student–project pair. The objective is a weighted sum set by the strategy.
- **Why:** it represents every hard constraint exactly, and it can *prove* when no further distinct alternative exists (R5).
- **Library:** OPEN. Options: PuLP (bundles the CBC solver), Pyomo + highspy (familiar from the OR course), or `scipy.optimize.milp`. None of them is in `requirements.txt` yet, so the chosen one must be added.
- **Casper (2026-10-16):** suggests Pyomo + highspy, since both of us used it in TECH4 and can build on that material.
- **Decision:**

### D7. Rank value for an unranked project — OPEN
`Assignment.preference_rank` stays `None`. Metrics and the solver still need a number. Proposal: 1 + the longest preference list in the cohort.
- **Decision:**

### D8. Additional fairness indicator — OPEN
The brief requires one, "proposed and justified by the teams" (§5.3). Proposal: Gini coefficient of assigned ranks (`calculate_gini` already exists in the skeleton), plus rank variance.
- **Decision:**

### D10. Making alternatives meaningful — PROPOSED
The definition of "distinct" is fixed (R5). The choice is how to make alternatives differ in useful ways: run a different strategy for each one (PREFERENCE → SKILL_FIT → BALANCED).
- **Decision:**

### D11. Validation responses — OPEN
The brief asks us to decide, for each situation, whether to reject, warn, allow a partial result, or report infeasibility (§9). Rows fixed by the brief or tests are R6 and R7.

| Situation | Decision |
|---|---|
| Project has fewer qualified students than its minimum (mandatory skill; depends on Q2) | |
| Student qualifies for no project at all | |
| Tied ranks within one student's list | currently a warning |

### D12. Tie-breaking — PROPOSED
Equal objective values are expected (brief §9). Add a tiny fixed tie-break (e.g. by student order) so runs are reproducible for the demo, and document it in the analytical note.
- **Decision:**

### D13. Reporting unassigned students — OPEN (agree with Team A)
R1 allows unassigned students when capacity is short. Decide how the engine reports them (diagnostics field and wording) and how the UI shows them.
- **Decision:**

---

## Log

| Date | Decision | By |
|---|---|---|
| | | |
