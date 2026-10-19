# Team B decisions

The single record of modelling and policy decisions for the assignment engine. Agents and team members read this before engine work. When something is decided, change its status to **DECIDED**, write the decision and who approved it, and add a line to the log at the bottom.

Status values: **OPEN** (not decided) · **PROPOSED** (team's choice, awaiting approval) · **DECIDED**

---

## Needs instructor approval

### D1. Assignment method — OPEN
- **Proposal:** integer linear programming (ILP). One binary variable per eligible student–project pair. The objective is a weighted sum set by the strategy.
- **Why:** it represents every hard constraint exactly, and it can *prove* when no further distinct alternative exists (edge cases 14 and 15).
- **Library:** OPEN. Options: PuLP (bundles the CBC solver), Pyomo + highspy (familiar from the OR course), or `scipy.optimize.milp`. None of them is in `requirements.txt` yet, so the chosen one must be added.
- **Casper (2026-10-16):** suggests Pyomo + highspy, since both of us used it in TECH4 and can build on that material.
- **Approved by / date:**

### D2. Mandatory skills: per student or per project? — OPEN
- **Per student:** every student assigned to the project must meet the level. Ineligible pairs are simply excluded.
- **Per project:** at least one assigned student must meet the level. This forces projects with minimum 0 to be non-empty, unless projects can stay empty.
- **Hints:** `validation.py` checks "no student in the cohort has it" and the brief says "may leave another project without appropriate skills"; both lean per project. `docs/analytical_formulation.md` says "satisfied by assigned students", which leans per student.
- **Decision:**

### D3. Too few seats for all students — OPEN
- **Option a:** reject the input as infeasible. This is the current behaviour and what edge case 7 tests.
- **Option b:** allow unassigned students ("at most one project" in the brief). Unassigned students must not be stored as assignments (the foreign key to `projects`); report them in diagnostics instead, and agree with Team A how the UI shows them.
- **Decision:**

### D4. Updating the three stub-asserting tests — OPEN
They will fail once the engine works: `test_assignment_engine_initialization`, `test_assignment_engine_raises_not_implemented`, and the `NotImplementedError` checks in `tests/test_contract_and_engine.py`.
- **Decision:**

---

## Team decisions (agree with Team A where noted)

### D5. A fixed assignment that breaks a mandatory skill — OPEN
- **Options:** treat it as infeasible, or let the administrator's lock win and show a warning.
- **Decision:**

### D6. Fixed-assignment status values — OPEN
The UI offers `APPROVED`, `MANDATORY` and `CONDITIONAL`. Are all three hard locks? If `CONDITIONAL` is softer, what does it mean?
- **Decision:**

### D7. Rank value for an unranked project — OPEN
`Assignment.preference_rank` stays `None`. Metrics and the solver still need a number. Proposal: 1 + the longest preference list in the cohort.
- **Decision:**

### D8. Additional fairness indicator — OPEN
The brief requires one, proposed and justified by the team. Proposal: Gini coefficient of assigned ranks (`calculate_gini` already exists in the skeleton), plus rank variance.
- **Decision:**

### D9. Skill-fit score — fixed by the tests
- The score is the mean over a project's requirements of `min(1, level / minimum_level)`.
- No requirements gives 1.0; a student with no skills gives 0.0.
- `unmet_requirements` lists every requirement below the required level.
- Still OPEN: do mandatory requirements count in the score, or only soft ones?

### D10. What counts as a distinct alternative — PROPOSED
- At least one student's project changes, as in the brief. Implemented as an ILP cut against every earlier solution.
- Make alternatives meaningful by running a different strategy for each one (PREFERENCE → SKILL_FIT → BALANCED). Don't raise the minimum number of students that must move; that breaks edge case 15 and the brief's definition.

### D11. Validation gaps — OPEN
For each, decide: reject, warn, or allow.

| Situation | Decision |
|---|---|
| Student ranks fewer than 3 projects (the brief says at least 3) | |
| Skill level outside 1–5 | |
| Project has fewer qualified students than its minimum (mandatory skill) | |
| Student qualifies for no project at all | |
| Tied ranks within one student's list | currently a warning |

### D12. Tie-breaking — PROPOSED
Equal objective values are expected. Add a tiny fixed tie-break (e.g. by student order) so runs are reproducible for the demo, and document it in the analytical note.

---

## Log

| Date | Decision | By |
|---|---|---|
| | | |
