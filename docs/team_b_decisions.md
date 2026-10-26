# Team B decisions

The single record of modelling and policy rules for the assignment engine. Agents and team members read this before engine work.

The file has three parts:

1. **Requirements (R):** fixed by the challenge brief, the supplied tests, the starter code or the starter docs. Not up to us; implement them as written.
2. **Questions for the instructor:** items that need the instructor's sign-off.
3. **Decisions (D):** genuine choices for Team B. When one is made, change its status to **DECIDED**, write the decision and who approved it, and add a line to the log at the bottom.

Status values for decisions: **OPEN** (not decided) · **PROPOSED** (team's choice, awaiting approval) · **DECIDED**

Decision IDs are kept stable. Missing IDs (D2–D13 except D1) turned out to be requirements or were withdrawn; each requirement says which ID it replaced.

## Source check (do this before adding or changing any item)

An item may only be listed as a decision after **all** of these sources have been checked and none of them fixes it:

1. The challenge brief (`TECH5_Collaborative_Project.pdf`, cited as "brief §n").
2. The supplied tests in `tests/` (they must pass, brief §10.3).
3. The contract, domain objects and database schema: `app/contract/contract.py`, `app/domain/models.py`, `app/persistence/schema.sql` (its `CHECK`, `UNIQUE` and key constraints define what valid data is).
4. The starter code that consumes engine output: `app/engine/recommendations.py`, `app/engine/metrics.py` and `solvers.py` docstrings, `app/visualization/` routes and templates.
5. The starter docs: `README.md` and every file in `docs/`. Start with the edge-case table in `docs/testing_and_quality.md` §2, which states the expected handling of all 15 edge cases. In `docs/analytical_note_template.md`, text outside `[brackets]` is given.

If a source fixes the item, it is a requirement: cite the source. If sources conflict, the order is **tests > brief > contract, schema and starter code > docs**, because the tests must pass; record the conflict in the requirement.

---

## 1. Requirements

### R1. Every student gets exactly one project; too few seats is infeasible (was D3)
- Too few seats in total, or too many minimum seats, is reported as **infeasible** with diagnostics. (`tests/test_validation.py::test_aggregate_capacity_deficit`, `tests/test_edge_cases.py` cases 7 and 8, `tests/test_contract_and_engine.py::test_contract_validate_inputs`, `docs/testing_and_quality.md` cases 7 and 8)
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
- With ILP this is a no-good cut against every earlier solution, $\sum_{(s,p) \in A^{(k)}} x_{s,p} \le |S| - 1$. Do not require more than one student to move. (`docs/testing_and_quality.md` case 15)

### R6. Incomplete preferences are allowed (was a D11 row)
- The brief says students rank at least three projects (§4), but edge case 1 requires a student with a single ranking to get a solution, and the UI accepts a student with one preference (`tests/test_visualization_component.py::test_create_student_preference_validation`).
- So fewer than three rankings is a **warning**, not a rejection. Unranked projects get the penalty rank in R14.

### R7. Valid skill levels are 1–5; anything else is rejected (was D11)
- Levels run from 1 to 5. (brief §4)
- The database stores only levels ≥ 1 for student skills and requirements (`schema.sql`, `CHECK(level >= 1)`, `CHECK(minimum_level >= 1)`). A student without a skill has no row; `Student.get_skill_level` then returns 0.
- A level above 5 is outside the scale the brief defines, and Team A's requirement form allows at most 5. Validation **rejects** any stored level outside 1–5.

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
- Indicator keys read by `recommendations.py` and the templates: listed under "Team B notes" in `AGENTS.md`, plus `fairness.rank_variance` and `fairness.unranked_pct`.
- `compare_two_solutions` returns at least `is_distinct`, `changed_students_count`, `delta_mean_skill_fit`, `delta_mean_rank` and `rank_worsened_count`. (`tests/test_metrics.py::test_solution_comparison`)

### R12. Preference lists must be valid; ties are rejected (was D11)
- One rank per project and one project per rank for each student, ranks ≥ 1. (`schema.sql`: primary key `(student_id, project_id)`, `UNIQUE (student_id, rank)`, `CHECK(rank >= 1)`)
- Validation **rejects** tied ranks or a repeated project within one student's list. `validation.py` currently only warns for both and must be changed.
- Students sharing the same preferences ("tied preferences across students", brief §9) are valid and must solve (edge case 2).

### R13. Mandatory skills apply per project (was D2 / Q2)
- Each mandatory requirement must be met by **at least one** student assigned to the project: $\sum_{s \in Q_{p,k}} x_{s,p} \ge 1$, where $Q_{p,k}$ is the set of students qualified for mandatory skill $k$ on project $p$. (`docs/analytical_note_template.md` §2.4: "guaranteeing that any mandatory project requirement is satisfied by at least one assigned student")
- Consistent with brief §4 ("may leave another project without appropriate skills") and with validation's cohort-level check (edge case 12).
- If a project with a mandatory requirement may stay empty ($l_p = 0$), the constraint applies only when the project is used.

### R14. Unranked projects count as rank |P| + 1 (was D7)
- A student assigned to a project they did not rank gets penalty rank $|P| + 1$ in the solver and the metrics, with Borda weight 0. (`docs/testing_and_quality.md` case 1, `docs/analytical_note_template.md` §2.2)
- `Assignment.preference_rank` stays `None` for these students, and they are counted in `fairness.unranked_count`.

### R15. Each alternative uses a different strategy (was D10)
- Alternative 1 uses the requested `strategy_key` (the UI's "primary strategy"); later alternatives use the remaining strategies in turn, for example PREFERENCE → SKILL_FIT → BALANCED, each with no-good cuts against all earlier solutions (R5). (`docs/reproducible_demonstration.md` §2.3, strategy pattern in `docs/architecture.md` §4.1)
- This gives each recommendation in `recommendations.py` a real candidate.

### R16. Results are deterministic (was D12)
- Ties are resolved deterministically, using skill fit and the cohort-level objective. (`docs/testing_and_quality.md` case 2)
- The same input gives the same solutions, so the demonstration is reproducible (brief §11, item 8). Any remaining exact tie is broken in a fixed order (for example by student ID), documented in the analytical note.

### R17. Unknown skill IDs give a warning
- A student or project referring to a skill missing from the catalogue gives a **warning**. (`tests/test_edge_cases.py::test_edge_case_6_unknown_skill_in_entity`)
- Conflict noted: `docs/testing_and_quality.md` case 6 says "rejection". The test wins.

---

## 2. Questions for the instructor

### Q1. Approval of the assignment method
The brief requires instructor approval before the method becomes the baseline (§7). Send the D1 proposal, and mention R13 (mandatory skills per project) so the instructor sees the full model.
- **Approved by / date:** Professor Julio Goez, 2026-10-22. Approved ILP with Pyomo + highspy, including R13
---

## 3. Team B decisions

### D1. Assignment method and library — DECIDED
- **Method:** integer linear programming (ILP). One binary variable per student–project pair. The objective is a weighted sum set by the strategy.
- **Why:** it represents every hard constraint exactly, and it can *prove* when no further distinct alternative exists (R5).
- **Library: Pyomo + highspy** (HiGHS solver). Casper proposed it (2026-10-16), Victor agreed (2026-10-19). We both used Pyomo with `appsi_highs` in TECH4. Both packages must be added to `requirements.txt`. The starter docs mention PuLP/CBC only as an example.

### D14. Arguments of `calculate_cost_or_utility` — DECIDED
- **Decision:** the abstract method in `AssignmentStrategy` takes `(data, s, p)` instead of the starter's `(student, project, max_preferences)`. It still returns the objective coefficient of `x[s,p]`, so the strategy pattern of `docs/architecture.md` §4.1 is unchanged.
- **Why:** the coefficients need r, φ and σ, which `prepare_data` already computes, plus the cohort size n (tie-break weights ε) and the project count m (penalty rank m + 1, R14). The starter arguments carry neither n nor m, and `max_preferences` (most projects any student ranked) is not m.
- **Impact:** none outside `app/engine/solvers.py`. Checked on every branch and open pull request (2026-10-22): no code, template or test calls the method; `test_assignment_strategy_abc` still holds because the method stays abstract.
- **Proposed by:** Victor (2026-10-22). Confirmed by Casper (2026-10-26) after the solver pull requests (#10-13) were merged. 

---

### D15. Indicator conventions in `metrics.py` — DECIDED
- **Variance:** `rank_variance` is the population variance, $\frac{1}{n}\sum_s (r_s - \bar{r})^2$, because we describe the whole cohort, not a sample.
- **Rounding:** means, variance and Gini are rounded to 4 decimals; percentages to 1 decimal. Comparison deltas are rounded to 4 decimals, so 0.95 − 0.55 gives 0.4, not 0.39999.
- **Proposed by:** Casper (2026-10-26), in the indicators pull request.

---

## Log

| Date | Decision | By |
|---|---|---|
| 2026-10-19 | D1 library: Pyomo + highspy | Casper, Victor |
| 2026-10-22 | D14 proposed: strategy coefficient reads from `prepare_data` | Victor |
| 2026-10-22 | Q1: method approved by instructor | Professor Julio Goez |
| 2026-10-26 | D14 confirmed | Casper |
| 2026-10-26 | D15: population variance, rounding | Casper |
