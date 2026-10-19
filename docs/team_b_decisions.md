# Team B decisions

The single record of modelling and policy rules for the assignment engine. Agents and team members read this before engine work.

The file has three parts:

1. **Requirements (R):** fixed by the challenge brief, the supplied tests or the starter code. Not up to us; implement them as written.
2. **Questions for the instructor:** the sources leave them open, but they are not ours to settle.
3. **Decisions (D):** genuine choices for Team B. When one is made, change its status to **DECIDED**, write the decision and who approved it, and add a line to the log at the bottom.

Status values for decisions: **OPEN** (not decided) · **PROPOSED** (team's choice, awaiting approval) · **DECIDED**

Decision IDs are kept stable. Gaps (D2–D6, D8, D9, D11, D13) are items that turned out to be requirements, questions or withdrawn.

## Source check (do this before adding or changing any item)

An item may only be listed as a decision after **all** of these sources have been checked and none of them fixes it:

1. The challenge brief (`TECH5_Collaborative_Project.pdf`, cited as "brief §n").
2. The supplied tests in `tests/` (they must pass, brief §10.3).
3. The contract, domain objects and database schema: `app/contract/contract.py`, `app/domain/models.py`, `app/persistence/schema.sql` (its `CHECK`, `UNIQUE` and key constraints define what valid data is).
4. The starter code that consumes engine output: `app/engine/recommendations.py`, `app/engine/metrics.py` and `solvers.py` docstrings, `app/visualization/` routes and templates.
5. The starter docs: `README.md`, `docs/analytical_note_template.md` (text outside `[brackets]` is given), `docs/analytical_formulation.md`, `docs/reproducible_demonstration.md`.

If a source fixes the item, it is a requirement: cite the source. If sources conflict, the order is **tests > brief > contract and starter code > docs**, because the tests must pass; record the conflict in the requirement.

---

## 1. Requirements

### R1. Every student gets exactly one project; too few seats is infeasible (was D3)
- Too few seats in total, or too many minimum seats, is reported as **infeasible** with diagnostics. (`tests/test_validation.py::test_aggregate_capacity_deficit`, `tests/test_edge_cases.py` cases 7 and 8, `tests/test_contract_and_engine.py::test_contract_validate_inputs`)
- `RunRequest` has no option for a partial allocation, so the engine never leaves a student unassigned.
- Conflict noted: brief §4 says "at most one project, or exactly one where total project capacity makes this possible", which would allow unassigned students. The supplied tests require infeasibility instead, and they win (brief §10.3).

### R2. Hard constraints are never relaxed (was D5)
- Hard constraints: capacity limits, mandatory skills, valid identifiers, one project per student, fixed assignments. (brief §5.1)
- If they cannot all hold, for example a fixed assignment that blocks a mandatory skill, the result is **infeasible with diagnostics** naming the conflict. "Do not hide the problem or silently change the constraints." (brief §5.1)
- This also covers "project has too few qualified students" and "student qualifies for no project": both are infeasible with diagnostics, whether validation or the solver detects them.

### R3. Fixed assignments are always preserved (was D6)
- The application must "preserve administrative fixed assignments". (brief §2, §5.1)
- All statuses offered by the UI (`APPROVED`, `MANDATORY`, `CONDITIONAL`) are hard locks. The status records why a student is locked; it does not change the constraint.

### R4. Skill fit uses non-mandatory requirements (was D9)
- "Mandatory requirements act as hard constraints, while non-mandatory requirements contribute to skill-fit assessment." (brief §4)
- Score per student–project pair: mean over the project's non-mandatory requirements of `min(1, level / minimum_level)`. No such requirements gives 1.0; a student with no skills gives 0.0. (`tests/test_metrics.py::test_skill_fit_calculation`, edge cases 3 and 4)
- `unmet_requirements` lists every requirement below the required level.

### R5. Distinct alternatives (was the definition part of D10)
- Up to K distinct feasible solutions, default K = 3. Two solutions differ only when at least one student's project changes. (brief §6, `tests/test_solvers.py::test_distinct_alternatives_generation`)
- If fewer distinct solutions exist, return only those and set `run.diagnostics["distinct_alternatives"]` to the number found; never duplicate one. (brief §6, edge cases 14 and 15)
- With ILP this is a no-good cut against every earlier solution. Do not require more than one student to move.

### R6. Incomplete preferences are allowed, with a warning (was a D11 row)
- The brief says students rank at least three projects (§4), but edge case 1 requires a student with a single ranking to get a solution, and the UI accepts a student with one preference (`tests/test_visualization_component.py::test_create_student_preference_validation`).
- So fewer than three rankings is a **warning**, not a rejection.

### R7. Valid skill levels are 1–5; anything else is rejected (was D11)
- Levels run from 1 to 5. (brief §4)
- The database stores only levels ≥ 1 for student skills and requirements (`schema.sql`, `CHECK(level >= 1)`, `CHECK(minimum_level >= 1)`). A student without a skill has no row; `Student.get_skill_level` then returns 0.
- A level above 5 is outside the scale the brief defines, and Team A's requirement form allows at most 5. Validation **rejects** any stored level outside 1–5.

### R12. Preference lists must be valid; ties are rejected (was D11)
- One rank per project and one project per rank for each student, ranks ≥ 1. (`schema.sql`: primary key `(student_id, project_id)`, `UNIQUE (student_id, rank)`, `CHECK(rank >= 1)`)
- Validation **rejects** tied ranks or a repeated project within one student's list. `validation.py` currently only warns for both and must be changed.
- Students sharing the same preferences ("tied preferences across students", brief §9) are valid and must solve (edge case 2).

### R8. The supplied test suite must pass (was D4)
- "The supplied automated test suite must pass without unexpected failures or regressions." (brief §10.3)
- Three tests assert the unimplemented stubs: `test_assignment_engine_initialization`, `test_assignment_engine_raises_not_implemented`, and the `NotImplementedError` checks in `tests/test_contract_and_engine.py`. When the engine replaces the stubs, update each one to check the real behaviour instead (for example, three strategies instead of zero), and say so in the pull request. This entry is the approval AGENTS.md rule 2 refers to.

### R9. Additional fairness indicator: Gini of ranks, plus rank variance (was D8)
- The starter code fixes the choice: `calculate_gini` is a listed Team B task (`README.md`) and is tested (`tests/test_metrics.py::test_gini_calculation`); `recommendations.py` selects the balanced recommendation by `rank_gini` then `rank_variance`; the templates display both.
- Our part is the justification in the analytical note (brief §5.3: "proposed and justified"): Gini measures inequality between students, which the mean rank, worst rank and unranked count do not.

### R10. Run outcomes
- A solved run has `status == "COMPLETED"` and at least one solution. (edge cases 1–4, 14, 15)
- An infeasible run has `status == "INFEASIBLE"` and no solutions; it is returned, not raised. (edge case 13, brief §5.1)
- Each solution records the `strategy_name` that produced it. (`models.Solution`, templates)

### R11. Output keys are fixed
- Indicator keys read by `recommendations.py` and the templates: listed under "Team B notes" in `AGENTS.md`, plus `fairness.rank_variance`.
- `compare_two_solutions` returns at least `is_distinct`, `changed_students_count`, `delta_mean_skill_fit`, `delta_mean_rank` and `rank_worsened_count`. (`tests/test_metrics.py::test_solution_comparison`)

---

## 2. Questions for the instructor

### Q1. Approval of the assignment method (part of D1)
The brief requires instructor approval before the method becomes the baseline (§7). Send the D1 proposal.
- **Approved by / date:**

### Q2. Mandatory skills: per student or per project? (was D2)
The brief says mandatory requirements are hard constraints (§4) but not whom they apply to. The template allows either ("satisfied by at least one assigned student, or explain how your solver handles this", §2.4).
- **Per student:** every student assigned to the project must meet the level. Ineligible pairs are simply excluded.
- **Per project:** at least one assigned student must meet the level.
- **Team B proposal: per project.** It matches the brief's trade-off "may leave another project without appropriate skills" (§4), the template's wording, and the existing validation check (no student in the cohort has the skill). Victor agrees (2026-10-19); Casper to confirm.
- **Answer:**

---

## 3. Team B decisions

### D1. Assignment method and library — library DECIDED, method awaiting Q1
- **Method:** integer linear programming (ILP). One binary variable per student–project pair. The objective is a weighted sum set by the strategy.
- **Why:** it represents every hard constraint exactly, and it can *prove* when no further distinct alternative exists (R5).
- **Library: Pyomo + highspy** (HiGHS solver). Casper proposed it (2026-10-16), Victor agreed (2026-10-19). We both used Pyomo with `appsi_highs` in TECH4. Both packages must be added to `requirements.txt`. The README's "e.g. PuLP/CBC" is an example, not a requirement.

### D7. Rank value for an unranked project — OPEN
`Assignment.preference_rank` stays `None`. Metrics and the solver still need a number.
- **(a) 1 + the longest preference list in the cohort.** Victor's preference (2026-10-19): unranked is one step worse than the worst real choice, so averages are not inflated.
- **(b) |P| + 1.** `docs/analytical_note_template.md` §2.2 defines $r_{s,p} \in \{1,\dots,|P|\} \cup \{|P|+1\}$ outside the brackets, so the instructor may expect this.
- Not fixed by any test. If we choose (a), the analytical note must say we depart from the template and why.
- **Decision:**

### D10. Strategies across alternatives — PROPOSED
Constraint: `RunRequest` carries one `strategy_key`, which the UI calls the "primary strategy", so alternative 1 uses it.
- **Proposal:** later alternatives use the remaining strategies in turn (for example PREFERENCE → SKILL_FIT → BALANCED), each with no-good cuts against all earlier solutions (R5). This is what `docs/reproducible_demonstration.md` §2.3 shows, and it makes `recommendations.py` meaningful because each policy has a candidate.
- **Alternative:** all alternatives use the primary strategy, giving the next-best solutions under one objective. These often differ by one or two students, so the trade-off the brief asks to show (§6) is weak.
- Victor prefers the proposal (2026-10-19); Casper to confirm.
- **Decision:**

### D11. Validation responses — WITHDRAWN
Every row turned out to be fixed by a source: capacity (R1), infeasible combinations (R2), incomplete preferences (R6), skill levels (R7), and tied or repeated preferences (R12).

### D12. Tie-breaking — PROPOSED
Equal objective values are expected (brief §9). Add a tiny fixed tie-break (e.g. by student order) so runs are reproducible for the demo (brief §11, item 8), and document it in the analytical note.
- **Decision:**

### D13. Reporting unassigned students — WITHDRAWN
Added on 2026-10-19 on the assumption that students could be left unassigned. R1 shows the tests require infeasibility instead, so there are no unassigned students to report.

---

## Log

| Date | Decision | By |
|---|---|---|
| 2026-10-19 | D1 library: Pyomo + highspy | Casper, Victor |
