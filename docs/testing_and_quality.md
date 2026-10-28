# TECH5 Assignment Support System: Testing, Quality Assurance & Edge Cases Report

## 1. Quality Assurance & Test Strategy Overview

The TECH5 Student-to-Project Assignment Decision Support System implements a comprehensive multi-tier automated test suite built with `pytest`. The testing architecture ensures verification across four distinct layers:

```
+-------------------------------------------------------------------------+
|                  Layer 4: Component Integration Tests                   |
| (test_component_integration.py: E2E workflow, UI -> Engine -> Persistence) |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                    Layer 3: Contract Compliance Tests                   |
| (test_contract_and_engine.py: DTO typing, ABC interface, mock swap)      |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                   Layer 2: Edge Cases & Robustness Tests                |
| (test_edge_cases.py: 15 Section-13 failure & boundary conditions)       |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  Layer 1: Unit, Persistence & Solver Tests              |
| (test_models, test_validation, test_persistence, test_solvers, metrics) |
+-------------------------------------------------------------------------+
```

### Execution Summary
- **Test Framework**: `pytest 9.1.1` on Python 3.10.4.
- **Optimization Framework**: Pyomo with the HiGHS solver.
- **Total Tests**: 75 automated tests.
- **Test Results**: 75 passed, 0 failed, 0 xfailed.
- **Execution Time**: 4.51 seconds.
- **Execution Command**: `py -m pytest -v`


### Test Coverage

The automated test suite covers four main testing categories:

- **Component tests:** Verify individual system components, including validation, optimization, metrics, and user interface functionality.
- **Database tests:** Verify database initialization, persistence, and retrieval of students, projects, runs, and solutions (`tests/test_persistence.py`).
- **Integration tests:** Verify that the system components work together, including the complete assignment workflow and infeasible scenarios (`tests/test_component_integration.py` and `tests/test_contract_and_engine.py`).
- **Edge-case tests:** Verify the 15 boundary conditions documented in Section 13 of the analytical note (`tests/test_edge_cases.py`).

---

## 2. Test Suite Architecture & File Breakdown


| Test Module | Test Count | Focus & Responsibilities |
|---|:---:|---|
| `tests/test_component_integration.py` | 2 | End-to-end integration, assignment runs, fixed locks, reruns, and infeasibility handling. |
| `tests/test_contract_and_engine.py` | 5 | Contract compliance, execution, persistence, retrieval, and mock compatibility. |
| `tests/test_edge_cases.py` | 15 | All 15 required edge cases from Section 13 of the specification. |
| `tests/test_metrics.py` | 4 | Gini coefficient, skill fit, solution indicators, and comparisons. |
| `tests/test_models.py` | 4 | Domain models, serialization, and helper methods. |
| `tests/test_persistence.py` | 3 | SQLite schema initialization and database repository operations. |
| `tests/test_solvers.py` | 9 | Optimization strategies, distinct alternatives, input handling, and solver behaviour. |
| `tests/test_team_a_compare.py` | 9 | Comparison interface, missing solutions, invalid selections, and display behaviour. |
| `tests/test_validation.py` | 16 | Input validation, preference ranks, skill levels, capacities, and fixed assignments. |
| `tests/test_visualization_component.py` | 8 | Dashboard, role switching, CRUD workflows, and optimization interface. |
| **Total** | **75** | **75 passed, 0 failed.** |

---

## 3. Section 13 Edge Cases Verification Matrix

Section 13 of the project specification dictates that the system must handle 15 specific edge cases. The table below documents the system response and the automated test verifying each condition:

| # | Edge Case / Boundary Condition | System Handling Category | System Action & Diagnostic Behavior | Verifying Test Case |
|---|---|---|---|---|
| **1** | Incomplete student preferences (fewer ranked projects than total $|P|$) | Valid / Partial (with penalty) | Unranked projects assigned penalty rank $|P|+1$ (Borda weight = 0); student remains assignable. | `test_edge_case_1_incomplete_preferences` |
| **2** | Tied preferences across students (multiple students rank the same project first) | Handled by Optimizer | The solver accepts identical preference profiles and produces a completed allocation while respecting project capacity constraints. | `test_edge_case_2_tied_preferences_across_students` |
| **3** | Student with zero reported skills | Valid / Degraded Fit | Student assigned default skill level 0; skill fit scores 0.0; student remains assignable. | `test_edge_case_3_zero_skills_student` |
| **4** | Project with zero skill requirements | Valid / Neutral Fit | Project has empty requirements $K_p = \emptyset$; skill fit defaults to 1.0 (perfect fit). | `test_edge_case_4_zero_requirements_project` |
| **5** | Unknown project identifier in preference list | Rejection | Input validation rejects request before solver runs; reports unknown project ID. | `test_edge_case_5_unknown_project_in_preferences` |
| **6** | Unknown skill identifier in requirements or proficiency | Warning / Accepted | Input validation generates warnings identifying skills missing from the catalogue. The input is not rejected solely because a skill identifier is unknown. | `test_edge_case_6_unknown_skill_in_entity` |
| **7** | Aggregate project capacity deficit ($\sum u_p < \|S\|$) | Rejection / Infeasibility | Validation catches deficit before solver execution; issues diagnostic error. | `test_edge_case_7_aggregate_capacity_deficit` |
| **8** | Aggregate minimum capacity exceeds cohort size ($\sum l_p > \|S\|$) | Rejection / Infeasibility | Validation catches lower-bound impossibility; prevents solver launch. | `test_edge_case_8_aggregate_min_capacity_excess` |
| **9** | Project capacity inversion ($l_p > u_p$) | Rejection | Schema CHECK constraint and domain validation reject invalid project capacity bounds. | `test_edge_case_9_capacity_inversion` |
| **10** | Contradictory fixed locks (same student locked to 2 projects) | Rejection | Input validation rejects a student locked to two different projects and reports a contradictory fixed assignment. Identical duplicate locks are reported separately. | `test_edge_case_10_conflicting_fixed_locks_same_student` |
| **11** | Fixed locks exceeding project capacity ($\lvert F_p \rvert > u_p$) | Infeasibility Report | Input validation detects that fixed assignments exceed the project's maximum capacity and reports infeasibility with an explanatory error message. | `test_edge_case_11_fixed_locks_exceeding_project_capacity` |
| **12** | Unavailable mandatory skill across cohort | Infeasibility Report | Input validation detects that no student meets the mandatory skill requirement and reports infeasibility before optimization. | `test_edge_case_12_unavailable_mandatory_skill` |
| **13** | Infeasible assignment (one student, minimum capacity of two) | Infeasibility Report | The assignment engine returns status `INFEASIBLE` and no solutions. In this example, the capacity pre-check detects the problem before optimization. | `test_edge_case_13_no_feasible_solution` |
| **14** | Cohort admits exactly one feasible solution | Single Solution Handled | Solves Alternative 1; second iteration detects no further solutions; returns 1 solution. | `test_edge_case_14_single_feasible_solution` |
| **15** | Duplicate alternatives avoidance | Handled via Cuts | Integer no-good cuts ($\sum x_{s,p} \le \|S\|-1$) enforce that each alternative differs for $\ge 1$ student. | `test_edge_case_15_duplicate_avoidance_no_good_cuts` |

---

## 4. Contract Compliance & Mock Substitutability Evidence

A critical architectural requirement from Section 10 is that Component A and Component B integrate strictly through an abstract Python interface, allowing independent testing and mock substitution:

The contract is verified in `tests/test_contract_and_engine.py`. The tests confirm that the real `AssignmentEngine` implements `AssignmentEngineContract`, validates inputs, executes and retrieves runs, and supports solution comparisons.

The tests also verify that `MockAssignmentEngine` remains available as an implementation of the same contract. This allows components to be tested independently without requiring the real optimization engine in every test.

Both real and mock engines implement identical method signatures and return strongly typed DTOs (`ValidationOutcome`, `RunOutcome`, `RunComparison`), ensuring total isolation.

---

## 5. End-to-End Component Integration Evidence

The test suite includes full lifecycle integration tests in `tests/test_component_integration.py`:
1. **Full Lifecycle Test (`test_full_lifecycle_integration`)**:
   - Seeds standard benchmark data into SQLite.
   - Component A calls `engine.execute_run()` via `contract.RunRequest`.
   - Verifies 3 distinct alternatives generated and persisted with valid status `COMPLETED`.
   - Evaluates solution retrieval, metric calculations, and transparent recommendations.
   - Performs side-by-side solution comparison via `engine.compare_solutions()`.
   - Adds an administrative fixed assignment (`S02` to `P2`).
   - Triggers an optimization rerun: verifies the lock is strictly enforced in all new solutions and re-allocations are audited.
2. **Infeasibility Integration Test (`test_infeasible_cohort_integration`)**:
   - Loads an infeasible cohort with 10 students but only 6 available project places.
   - Invokes engine execution via the contract.
   - Verifies graceful handling: run status is `INFEASIBLE`, diagnostic message clearly explains the failure, and zero partial or corrupt solutions are saved.

---

## 6. Complete Pytest Execution Log


The complete test suite was run locally on 28 October 2026 using Python 3.10.4 and pytest 9.1.1. The tests were run on the `team-b/week3-documentation` branch, created from the latest `main`.

Command:

```bash
py -m pytest -v
```

Result:

```text
==================================================== test summary ====================================================
75 passed in 4.51s
```

All 75 tests passed, with no failures or expected failures. The suite includes component, database, integration, and edge-case tests.

### Full pytest output

```text

============================= test session starts =============================
platform win32 -- Python 3.10.4, pytest-9.1.1, pluggy-1.7.0 -- C:\Program Files\Python3.10\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\olekska\TECH5-Group5-6-CollabProject
collecting ... collected 75 items

tests/test_component_integration.py::test_full_lifecycle_integration PASSED [  1%]
tests/test_component_integration.py::test_infeasible_cohort_integration PASSED [  2%]
tests/test_contract_and_engine.py::test_engine_implements_contract PASSED [  4%]
tests/test_contract_and_engine.py::test_contract_validate_inputs PASSED  [  5%]
tests/test_contract_and_engine.py::test_contract_execute_and_retrieval PASSED [  6%]
tests/test_contract_and_engine.py::test_contract_compare_solutions PASSED [  8%]
tests/test_contract_and_engine.py::test_mock_engine_provided PASSED      [  9%]
tests/test_edge_cases.py::test_edge_case_1_incomplete_preferences PASSED [ 10%]
tests/test_edge_cases.py::test_edge_case_2_tied_preferences_across_students PASSED [ 12%]
tests/test_edge_cases.py::test_edge_case_3_zero_skills_student PASSED    [ 13%]
tests/test_edge_cases.py::test_edge_case_4_zero_requirements_project PASSED [ 14%]
tests/test_edge_cases.py::test_edge_case_5_unknown_project_in_preferences PASSED [ 16%]
tests/test_edge_cases.py::test_edge_case_6_unknown_skill_in_entity PASSED [ 17%]
tests/test_edge_cases.py::test_edge_case_7_aggregate_capacity_deficit PASSED [ 18%]
tests/test_edge_cases.py::test_edge_case_8_aggregate_min_capacity_excess PASSED [ 20%]
tests/test_edge_cases.py::test_edge_case_9_capacity_inversion PASSED     [ 21%]
tests/test_edge_cases.py::test_edge_case_10_conflicting_fixed_locks_same_student PASSED [ 22%]
tests/test_edge_cases.py::test_edge_case_11_fixed_locks_exceeding_project_capacity PASSED [ 24%]
tests/test_edge_cases.py::test_edge_case_12_unavailable_mandatory_skill PASSED [ 25%]
tests/test_edge_cases.py::test_edge_case_13_no_feasible_solution PASSED  [ 26%]
tests/test_edge_cases.py::test_edge_case_14_single_feasible_solution PASSED [ 28%]
tests/test_edge_cases.py::test_edge_case_15_duplicate_avoidance_no_good_cuts PASSED [ 29%]
tests/test_metrics.py::test_gini_calculation PASSED                      [ 30%]
tests/test_metrics.py::test_skill_fit_calculation PASSED                 [ 32%]
tests/test_metrics.py::test_solution_indicators_calculation PASSED       [ 33%]
tests/test_metrics.py::test_solution_comparison PASSED                   [ 34%]
tests/test_models.py::test_skill_serialization PASSED                    [ 36%]
tests/test_models.py::test_student_model_helpers PASSED                  [ 37%]
tests/test_models.py::test_project_model PASSED                          [ 38%]
tests/test_models.py::test_solution_and_assignment PASSED                [ 40%]
tests/test_persistence.py::test_schema_init_and_skill_repo PASSED        [ 41%]
tests/test_persistence.py::test_student_and_project_persistence PASSED   [ 42%]
tests/test_persistence.py::test_run_and_solution_persistence PASSED      [ 44%]
tests/test_solvers.py::test_assignment_strategy_abc PASSED               [ 45%]
tests/test_solvers.py::test_assignment_engine_initialization PASSED      [ 46%]
tests/test_solvers.py::test_assignment_engine_raises_not_implemented PASSED [ 48%]
tests/test_solvers.py::test_distinct_alternatives_generation PASSED      [ 49%]
tests/test_solvers.py::test_rank_gaps_are_read_as_positions PASSED       [ 50%]
tests/test_solvers.py::test_uncatalogued_skill_is_a_warning_not_a_crash PASSED [ 52%]
tests/test_solvers.py::test_catalogue_names_are_not_overwritten PASSED   [ 53%]
tests/test_solvers.py::test_invalid_input_is_reported_before_infeasibility PASSED [ 54%]
tests/test_solvers.py::test_infeasible_run_lists_each_reason_once PASSED [ 56%]
tests/test_team_a_compare.py::test_compare_two_alternatives PASSED       [ 57%]
tests/test_team_a_compare.py::test_compare_link_without_parameters PASSED [ 58%]
tests/test_team_a_compare.py::test_compare_with_one_solution_picks_a_partner PASSED [ 60%]
tests/test_team_a_compare.py::test_compare_with_no_solutions PASSED      [ 61%]
tests/test_team_a_compare.py::test_compare_unknown_solutions PASSED      [ 62%]
tests/test_team_a_compare.py::test_compare_same_solution_twice PASSED    [ 64%]
tests/test_team_a_compare.py::test_compare_shows_names_and_unranked_moves PASSED [ 65%]
tests/test_team_a_compare.py::test_compare_single_solution_run PASSED    [ 66%]
tests/test_team_a_compare.py::test_compare_across_runs_warns PASSED      [ 68%]
tests/test_validation.py::test_empty_cohort_validation PASSED            [ 69%]
tests/test_validation.py::test_duplicate_identifiers PASSED              [ 70%]
tests/test_validation.py::test_capacity_errors PASSED                    [ 72%]
tests/test_validation.py::test_contradictory_fixed_assignments PASSED    [ 73%]
tests/test_validation.py::test_fixed_exceeding_capacity PASSED           [ 74%]
tests/test_validation.py::test_aggregate_capacity_deficit PASSED         [ 76%]
tests/test_validation.py::test_duplicate_preference_rank_is_invalid PASSED [ 77%]
tests/test_validation.py::test_invalid_student_skill_levels_are_rejected PASSED [ 78%]
tests/test_validation.py::test_valid_student_skill_levels_are_accepted PASSED [ 80%]
tests/test_validation.py::test_fewer_than_three_preferences_warns_without_rejecting PASSED [ 81%]
tests/test_validation.py::test_three_preferences_does_not_trigger_short_ranking_warning PASSED [ 82%]
tests/test_validation.py::test_duplicate_preferred_project_is_invalid PASSED [ 84%]
tests/test_validation.py::test_invalid_requirement_levels_are_rejected PASSED [ 85%]
tests/test_validation.py::test_valid_requirement_levels_are_accepted PASSED [ 86%]
tests/test_validation.py::test_ranks_below_one_are_rejected PASSED       [ 88%]
tests/test_validation.py::test_same_lock_twice_is_reported_as_duplicate PASSED [ 89%]
tests/test_visualization_component.py::test_dashboard_loads PASSED       [ 90%]
tests/test_visualization_component.py::test_role_switcher PASSED         [ 92%]
tests/test_visualization_component.py::test_student_and_fixed_assignment_workflow PASSED [ 93%]
tests/test_visualization_component.py::test_scenario_loading_and_optimization_trigger PASSED [ 94%]
tests/test_visualization_component.py::test_create_student_preference_validation PASSED [ 96%]
tests/test_visualization_component.py::test_skills_crud_workflow PASSED  [ 97%]
tests/test_visualization_component.py::test_projects_crud_workflow PASSED [ 98%]
tests/test_visualization_component.py::test_compare_solutions_view PASSED [100%]

============================= 75 passed in 4.51s ==============================
```
