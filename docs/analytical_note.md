# Deliverable 6: Analytical Note & Mathematical Formulation
## Student Submission Template — TECH5 Collaborative Project

**Team:** Group 5-6  
**Authors (Team B - Assignment Engine):** Victor Goller, Casper Waale, Ole Kristian Skaar  
**Authors (Team A - Visualization & Recommender):** Alex Solheim, Herman Kilde, Nils Lærum Harloff  
**Course:** TECH5 Programming & Application Design, NHH Norwegian School of Economics  
**Date:** 2 November 2026

---

## 1. Problem Definition & Mathematical Modeling Approach

### 1.1 Business Context & Decision Dilemma
Every semester a programme coordinator must place each student in exactly one project. Each project has a minimum and a maximum headcount, may need certain skills, and some students are already locked to a project by an administrative decision. Students rank the projects they want, and they report their skill levels. Assigning students to projects in this way is a well-studied problem in operations research; Rezaeinia et al. (2022) give the context for this course.

The coordinator faces a real conflict. Giving every student a high-ranked project is good for satisfaction, but it can leave a project without the skills it needs. Filling every project with the best-qualified students is good for project quality, but it can send many students to projects they did not want, and it can hit a few students much harder than the rest. No single allocation is best on all of these at once. The application therefore does not hand down one answer: it computes several distinct alternatives, measures each one on feasibility, efficiency, fairness and capacity (§3), shows what changes between two of them (§4), and recommends one per policy priority while leaving the final decision to the coordinator (§5).

### 1.2 Chosen Assignment Methodology & Academic Justification
We use **integer linear programming (ILP)**, modelled in Pyomo and solved with the HiGHS solver (D1). The instructor approved the method on 22 October 2026 (Q1). All three strategies share one model (§2): one binary variable per student–project pair, the same hard constraints, and a different objective per strategy.

**The main reason is that Team B already knows the method.** We learned to model and solve ILPs with Pyomo and HiGHS (`appsi_highs`) in TECH4 at NHH, and the code follows the same structure as there: sets and parameters as Python dictionaries, one constraint list per constraint family, and anything non-linear computed before the model is built. Every line can therefore be explained and checked by the team, which matters more to us than trying a method we have not used before. The starter docs mention PuLP/CBC only as an example.

ILP also fits the problem itself, for three reasons:

1. **Hard constraints hold exactly.** Headcounts, fixed assignments and mandatory skills are linear constraints, so every solution the solver returns respects them. Nothing is relaxed to get an answer: if they cannot all hold, the solver proves it and the run is reported as infeasible (R2).
2. **Distinct alternatives can be proved.** A no-good cut (§2.4, constraint 5) forces at least one student to move. When the model with the cuts becomes infeasible, no further distinct allocation exists, so the application never shows a duplicate as a new alternative (R5).
3. **The objectives are explicit.** Each strategy is a written objective function (§2.5), so the coordinator and the reviewers can see what each alternative optimises. A heuristic would give no guarantee of optimality, and a stable-matching method has no natural place for mandatory skills per project or for a skill-fit objective.

**Computational feasibility.** The model has $n \cdot m$ assignment variables plus at most $m + 1$ helper variables. On the standard demonstration cohort ($n = 10$, $m = 4$) each strategy solves in a few hundredths of a second. On random test cohorts of 150 students and 20 projects each strategy took under 0.15 s, and on 300 students and 30 projects under 0.4 s (single thread, laptop). A full run of three alternatives is therefore well within what a single-process Flask application can do while the user waits.

---

## 2. Mathematical Formulation

One model with three objective functions: the sets, parameters, variables and constraints (§2.1–2.4) are shared by all strategies; only the objective (§2.5) changes. Rules tagged R1–R17 refer to the requirements in `docs/team_b_decisions.md`, each traced to the brief, the tests, the schema or the starter docs; D-numbers are Team B's own decisions in the same file. The full formulation, with equation numbers that the code cites, is in `docs/model/ilp_formulation.tex`.

### 2.1 Index Sets & Dimensions
- $S = \{s_1, \dots, s_n\}$: students in the cohort, $\lvert S \rvert = n$.
- $P = \{p_1, \dots, p_m\}$: projects, $\lvert P \rvert = m$.
- $T$: catalogued skills, indexed by $t$. (The letter $K$ is reserved for the number of alternatives, as in the brief.)
- $F \subseteq S \times P$: fixed assignments (administrative locks).
- $T_p^{\text{soft}} \subseteq T$: non-mandatory skill requirements of project $p$.
- $E_p \subseteq T$: mandatory ("essential") skill requirements of project $p$.
- $Q_{p,t} = \{ s \in S : \alpha_{s,t} \ge \beta_{p,t} \}$: students qualified for mandatory requirement $t \in E_p$.
- $P^{E} = \{ p \in P : E_p \neq \emptyset \}$: projects with at least one mandatory requirement.
- $\Omega = (\text{PREFERENCE}, \text{SKILL\_FIT}, \text{BALANCED})$: the strategies, in order.

All sets are built in sorted identifier order, so the same input always produces the same model (R16).

### 2.2 Model Parameters
- $l_p \in \mathbb{Z}_{\ge 0}$, $u_p \in \mathbb{Z}_{\ge 1}$: minimum and maximum headcount of project $p$, $l_p \le u_p$.
- $\alpha_{s,t} \in \{0, 1, \dots, 5\}$: proficiency of student $s$ in skill $t$; $0$ means the skill is not held (R7).
- $\beta_{p,t} \in \{1, \dots, 5\}$: minimum level that project $p$ requires in skill $t$ (R7).
- $K \in \mathbb{Z}_{\ge 1}$: number of distinct alternatives requested, default $K = 3$ (`max_alternatives`, R5). Alternatives are indexed $k = 1, \dots, K$ (`alternative_number`).
- $r_{s,p}$: preference rank of student $s$ for project $p$; an unranked project gets the penalty rank $m + 1$ (R14):

$$
r_{s,p} =
\begin{cases}
\text{position of } p \text{ in the list of } s, & \text{if } s \text{ ranked } p,\\
m + 1, & \text{otherwise.}
\end{cases}
$$

The position is counted in order of stated rank: $1$ for the student's first choice, $2$ for the next, and so on. If a project is deleted after students ranked it, the gap in the stored ranks is skipped, so a ranked project never costs more than an unranked one (D16).

- $\phi_{s,p} \in [0, 1]$: normalised preference score, $1$ for a first choice and $0$ for an unranked project:

$$
\phi_{s,p} = \frac{m + 1 - r_{s,p}}{m}
$$

- $\sigma_{s,p} \in [0, 1]$: skill fit of student $s$ on project $p$, over the non-mandatory requirements only (R4):

$$
\sigma_{s,p} =
\begin{cases}
\dfrac{1}{\lvert T_p^{\text{soft}} \rvert} \displaystyle\sum_{t \in T_p^{\text{soft}}} \min\!\left(1, \frac{\alpha_{s,t}}{\beta_{p,t}}\right), & T_p^{\text{soft}} \neq \emptyset,\\[2ex]
1, & T_p^{\text{soft}} = \emptyset.
\end{cases}
$$

$r_{s,p}$, $\phi_{s,p}$ and $\sigma_{s,p}$ are data, computed before solving, so every objective below is linear in the decision variables.

### 2.3 Decision Variables
- $x_{s,p} \in \{0, 1\}$: $1$ if student $s$ is assigned to project $p$.
- $y_p \in \{0, 1\}$ for $p \in P^{E}$: $1$ if project $p$ is used (has at least one student). Needed only so that a project with $l_p = 0$ and a mandatory requirement may stay empty (R13).
- $\theta \in \mathbb{R}_{\ge 0}$: worst assigned rank, used only by the BALANCED strategy.

### 2.4 Hard Mathematical Constraints
These hold for every strategy. They are never relaxed; if they cannot all hold, the run is reported as infeasible with diagnostics (R2, R10).

1. **Exactly one project per student** (R1):

$$
\sum_{p \in P} x_{s,p} = 1 \qquad \forall s \in S
$$

2. **Headcount bounds** (R1):

$$
l_p \le \sum_{s \in S} x_{s,p} \le u_p \qquad \forall p \in P
$$

3. **Fixed assignments** (R3), whatever their status (`APPROVED`, `MANDATORY`, `CONDITIONAL`):

$$
x_{s,p} = 1 \qquad \forall (s, p) \in F
$$

4. **Mandatory skills, per project** (R13). If a project is used, each mandatory requirement is met by at least one assigned student:

$$
\sum_{s \in Q_{p,t}} x_{s,p} \ge y_p \qquad \forall p \in P^{E},\ t \in E_p
$$

$$
\sum_{s \in S} x_{s,p} \le u_p \, y_p \qquad \forall p \in P^{E}
$$

The second line forces $y_p = 1$ whenever the project has a student. If $l_p \ge 1$, constraint 2 already makes the project non-empty, so $y_p = 1$ and the requirement must be met.

5. **Distinct alternatives: no-good cuts** (R5). Let $\Gamma^{(j)} = \{ (s, p) : x^{(j)}_{s,p} = 1 \}$ be the pairs of the $j$-th alternative found. Before solving for alternative $k$ ($k = 2, \dots, K$), add for every earlier alternative:

$$
\sum_{(s, p) \in \Gamma^{(j)}} x_{s,p} \le n - 1 \qquad j = 1, \dots, k - 1
$$

Since $\lvert \Gamma^{(j)} \rvert = n$, at least one student must then move. If the model becomes infeasible, no further distinct alternative exists; the run returns the solutions found so far and reports their number in `diagnostics["distinct_alternatives"]` (R5).

### 2.5 Optimization Objectives & Strategies

**Order of strategies (R15).** Alternative 1 uses the strategy the user selects. Each next alternative uses the next strategy in $\Omega$, wrapping around, and adds the no-good cuts above. With PREFERENCE selected and $K = 3$: alternative 1 = PREFERENCE, 2 = SKILL_FIT, 3 = BALANCED.

**Ties (R16).** Each strategy has a secondary term with a small weight, so that among solutions equal on the main goal the one that is better on the other goal is chosen (`docs/testing_and_quality.md`, edge case 2). Any remaining exact tie is resolved by the fixed sorted model order and a single-threaded HiGHS run, so the same input gives the same result.

- **Strategy 1: PREFERENCE (minimise total rank)**

$$
\min \; Z_{\text{pref}} = \sum_{s \in S} \sum_{p \in P} r_{s,p} \, x_{s,p} \;-\; \varepsilon_{\text{pref}} \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \, x_{s,p},
\qquad \varepsilon_{\text{pref}} = \frac{1}{n + 1}
$$

The rank sum is an integer, and the skill term is at most $n \, \varepsilon_{\text{pref}} < 1$, so it can only break ties: it never makes the rank sum worse. Minimising the rank sum equals minimising the mean rank $\bar{r}$ reported by the indicators.

- **Strategy 2: SKILL_FIT (maximise total skill fit)**

$$
\max \; Z_{\text{skill}} = \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \, x_{s,p} \;+\; \varepsilon_{\text{skill}} \sum_{s \in S} \sum_{p \in P} \phi_{s,p} \, x_{s,p},
\qquad \varepsilon_{\text{skill}} = 10^{-3} / n
$$

The preference term is at most $10^{-3}$, so it breaks ties between solutions with (practically) equal skill fit. Unlike Strategy 1 this is not an exact guarantee, because skill-fit totals are not integers; we state this as a limitation.

- **Strategy 3: BALANCED (protect the worst-off, then balance)**. Solved in two stages, so no weight between fairness and efficiency has to be tuned:

  *Stage 1 (egalitarian):* minimise the worst assigned rank

$$
\theta^{*} = \min \; \theta \quad \text{s.t.} \quad \theta \ge \sum_{p \in P} r_{s,p} \, x_{s,p} \quad \forall s \in S, \quad \text{and constraints 1–5}
$$

  *Stage 2 (balance):* among solutions with that worst rank, maximise an equal mix of preference and skill fit

$$
\max \; Z_{\text{bal}} = \sum_{s \in S} \sum_{p \in P} \bigl( \lambda \, \phi_{s,p} + (1 - \lambda) \, \sigma_{s,p} \bigr) x_{s,p}
\quad \text{s.t.} \quad \sum_{p \in P} r_{s,p} \, x_{s,p} \le \theta^{*} \;\; \forall s \in S, \quad \text{constraints 1–5}, \quad \lambda = 0.5
$$

Both terms lie in $[0, 1]$ per student, so $\lambda = 0.5$ weighs them equally. Stage 1 matches the strategy's label in the UI ("Egalitarian Fairness"): nobody gets a worse rank than necessary.

The three objectives, $\lambda = 0.5$ and the two-stage form of BALANCED were reviewed and merged by Team B (pull request #10). In the code, each strategy returns the coefficient of $x_{s,p}$ through `calculate_cost_or_utility(data, s, p)` (D14).

### 2.6 Notation Summary
Each symbol has exactly one meaning in this note.

| Symbol | Meaning | In the code |
|---|---|---|
| $S$, $s$, $n$ | students, a student, number of students | `students` |
| $P$, $p$, $m$ | projects, a project, number of projects | `projects` |
| $T$, $t$ | skills, a skill | `Skill` |
| $T_p^{\text{soft}}$, $E_p$ | non-mandatory / mandatory requirements of $p$ | `requirements`, `is_mandatory` |
| $Q_{p,t}$ | students qualified for mandatory skill $t$ on $p$ | — |
| $P^{E}$ | projects with a mandatory requirement | — |
| $F$ | fixed assignments | `fixed_assignments` |
| $\Omega$ | ordered list of strategies | `strategies` |
| $K$, $k$, $j$ | number of alternatives, an alternative, an earlier alternative | `max_alternatives`, `alternative_number` |
| $\Gamma^{(j)}$ | student–project pairs of alternative $j$ | `excluded_solutions` |
| $l_p$, $u_p$ | minimum / maximum headcount | `min_capacity`, `max_capacity` |
| $\alpha_{s,t}$ | proficiency of $s$ in $t$ | `get_skill_level` |
| $\beta_{p,t}$ | required level of $t$ on $p$ | `minimum_level` |
| $r_{s,p}$ | preference rank ($m + 1$ if unranked) | — |
| $\phi_{s,p}$ | normalised preference score | — |
| $\sigma_{s,p}$ | skill fit | `calculate_assignment_skill_fit` |
| $x_{s,p}$, $y_p$, $\theta$ | assignment, project used, worst rank | — |
| $Z_{\text{pref}}$, $Z_{\text{skill}}$, $Z_{\text{bal}}$ | objective functions | — |
| $\varepsilon_{\text{pref}}$, $\varepsilon_{\text{skill}}$, $\lambda$ | tie-break weights, balance weight | — |
| $\bar{\sigma}$, $\bar{r}$, $r_{\max}$, $c_h$, $c_{\text{unr}}$, $G$, $\text{Util}_p$ | indicators (§3) | `indicators` |
| $\Delta$ | difference between two solutions (§4) | `delta_*` |

Tags R1–R17 are references to `docs/team_b_decisions.md`, not symbols.

---

## 3. Evaluation Indicators & Analytical Metrics

Define the mathematical formulation for all evaluation metrics implemented in `app/engine/metrics.py`:

All indicators are computed by `compute_solution_indicators` from a finished list of assignments, so every strategy is scored by the same function. Means, the rank variance and the Gini coefficient are rounded to 4 decimals; percentages are rounded to 1 decimal. Counts and the worst rank are integers. The output keys are fixed, because `recommendations.py` and the templates read them (R11).

### 3.1 Feasibility Indicators
- Allocation completeness: $\sum_{s \in S} \sum_{p \in P} x_{s,p} = |S|$

  The code checks the stronger per-student form, $\sum_{p \in P} x_{s,p} = 1$ for every $s \in S$ (R1), because a total of $\lvert S \rvert$ could hide one student assigned twice and another not at all. A missing or duplicate assignment, or an assignment that refers to an unknown student or project, is a violation.
- Capacity compliance check for all $p \in P$

  $$l_p \le \sum_{s \in S} x_{s,p} \le u_p \qquad \forall p \in P$$

  A breach of either bound is a violation.
- Fixed lock adherence check

  Every locked pair must appear in the solution: $x_{s,p} = 1$ for all $(s, p) \in F$ (R3).
- Mandatory requirement fulfillment count

  Per R13, each used project must have at least one assigned student who meets each of its mandatory requirements:

  $$\sum_{s \in Q_{p,t}} x_{s,p} \ge 1 \qquad \forall p \in P^{E} \text{ with } \sum_{s \in S} x_{s,p} \ge 1,\ t \in E_p$$

  Empty projects are skipped. The code does not report a count of fulfilled requirements; it adds one violation for each unmet (project, mandatory skill) pair.

The solution is feasible (`feasibility.is_feasible`) exactly when the list of violations is empty. The code also reports `assigned_count` and `total_students`.

### 3.2 Efficiency Indicators
- **Mean Skill-Fit Score ($\bar{\sigma}$):**
  $$\bar{\sigma} = \frac{1}{|S|} \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \cdot x_{s,p}$$

  $\sigma_{s,p}$ is the skill fit from §2.2 (R4): the mean of $\min(1, \alpha_{s,t} / \beta_{p,t})$ over the non-mandatory requirements $T_p^{\text{soft}}$, and $1$ if the project has none. Mandatory requirements are left out because they are hard constraints (§3.1). The code reads $\sigma_{s,p}$ from each assignment's stored `skill_fit_score`, which `calculate_assignment_skill_fit` sets, and divides by the number of assignments; in a complete solution that number is $\lvert S \rvert$. An empty solution gives $0$. Key: `efficiency.mean_skill_fit`, with the total $\sum_{s} \sum_{p} \sigma_{s,p} \, x_{s,p}$ in `efficiency.total_skill_fit_sum`.
- **Mean Preference Rank ($\bar{r}$):**
  $$\bar{r} = \frac{1}{|S|} \sum_{s \in S} \sum_{p \in P} r_{s,p} \cdot x_{s,p}$$

  $r_{s,p}$ includes the penalty rank $m + 1$ for unranked projects (R14). The code reports this value as a fairness indicator, `fairness.mean_rank` (§3.3).
- **Unmet Soft Requirements Count:** the number of (student, non-mandatory requirement) pairs where the assigned student is below the required level:

  $$\sum_{s \in S} \sum_{p \in P} x_{s,p} \, \bigl\lvert \{ t \in T_p^{\text{soft}} : \alpha_{s,t} < \beta_{p,t} \} \bigr\rvert$$

  Gaps in mandatory requirements are not counted here; §3.1 covers them. Key: `efficiency.unmet_soft_requirements_count`.

### 3.3 Fairness Indicators
*Section 6.3 of the specification mandates: rank distribution, unranked count, worst assigned rank, and ONE proposed and justified fairness indicator.*

Throughout, $r_s = \sum_{p \in P} r_{s,p} \, x_{s,p}$ is the rank that student $s$ receives. A student placed on a project they did not rank counts as rank $m + 1$ (R14) in the mean rank, the worst rank, the variance and the Gini coefficient. `Assignment.preference_rank` itself stays `None` for these students.

1. **Rank Distribution:** Histogram vector $[c_1, c_2, \dots, c_m, c_{\text{unr}}]$ where $c_h$ is the number of students assigned to their $h$-th choice.

   The code returns this as a sparse dictionary: a key `rank_h` appears only for ranks that occur, and `unranked` only when $c_{\text{unr}} > 0$; a missing key means a count of $0$.
2. **Unranked Allocation Count ($c_{\text{unr}}$):** Count of students allocated outside their submitted preference list.

   $$c_{\text{unr}} = \bigl\lvert \{ s \in S : r_s = m + 1 \} \bigr\rvert, \qquad \text{unranked\_pct} = \frac{c_{\text{unr}}}{n} \times 100\%$$
3. **Worst Assigned Rank ($r_{\max}$):**
   $$r_{\max} = \max_{(s,p) : x_{s,p}=1} r_{s,p}$$

   Because $r_{s,p}$ includes the penalty, $r_{\max} = m + 1$ whenever at least one student is unranked. An empty solution gives $0$.
4. **Team's Proposed Fairness Indicator (e.g., Gini Coefficient or Rank Variance):**
   *Provide the mathematical formula, justification, and interpretation:*
   With $r_s = \sum_{p \in P} r_{s,p} \, x_{s,p}$ the rank assigned to student $s$:
   $$G = \frac{\sum_{s \in S} \sum_{s' \in S} |r_s - r_{s'}|}{2 n \sum_{s \in S} r_s}$$

   We report the Gini coefficient of the assigned ranks (R9). The mean rank hides how outcomes are spread: two students who both get their second choice and two students who get their first and third choice have the same $\bar{r} = 2$, but Gini values of $0$ and $0.25$. Gini compares every pair of students, so it rises when some students do much better than others. $G = 0$ means every student received the same rank, and higher values mean more unequal outcomes (at most $(n - 1)/n$). Because the pairwise differences are divided by the total rank, $G$ is scale-independent: multiplying every rank by the same constant leaves it unchanged.

   `calculate_gini` returns $0$ for an empty list or a list of zeros, and rejects negative values. Since every $r_s \ge 1$, the denominator is positive for any non-empty solution. Key: `fairness.rank_gini`.

   As a second spread measure, the code reports the population variance of the assigned ranks (key `fairness.rank_variance`):

   $$\operatorname{Var}(r) = \frac{1}{n} \sum_{s \in S} \left( r_s - \bar{r} \right)^2$$

   We divide by $n$, not $n - 1$, because the cohort is the whole population, not a sample. The balanced recommendation in `recommendations.py` ranks solutions by Gini first and variance second (R9).

### 3.4 Capacity Utilization Metrics
- Per-project utilization percentage:
  $$\text{Util}_p = \frac{\sum_{s \in S} x_{s,p}}{u_p} \times 100\%$$

  A project with $u_p = 0$ reports $0$. Each project entry also reports `assigned_count`, `min_capacity` and `max_capacity`.
- Aggregate cohort capacity slack and tightness

  Overall utilization divides all assigned students by all seats:

  $$\text{Util} = \frac{\sum_{s \in S} \sum_{p \in P} x_{s,p}}{\sum_{p \in P} u_p} \times 100\%$$

  It is $0$ if there are no seats. Key: `capacity.overall_utilization_pct`. The code does not report slack as a separate key; it reports `total_assigned` and `total_capacity`, so the slack is $\sum_{p \in P} u_p - n$ seats. A value near $100\%$ means a tight instance with few spare seats.

---

## 4. Trade-Off Analysis & Solution Comparison

### 4.1 Comparative Delta Formulation
Explain how the system computes performance deltas between Solution A and Solution B:
$$\Delta \bar{\sigma} = \bar{\sigma}_B - \bar{\sigma}_A$$
$$\Delta \bar{r} = \bar{r}_B - \bar{r}_A$$
$$\Delta r_{\max} = r_{\max, B} - r_{\max, A}$$
$$\Delta G = G_B - G_A$$

`compare_two_solutions` takes each delta from the indicators already stored on the two solutions, always as B minus A, and rounds it to 4 decimals. The code does not compute $\Delta r_{\max}$; instead it reports the deltas of the rank variance and the unranked count:

$$\Delta \operatorname{Var}(r) = \operatorname{Var}(r)_B - \operatorname{Var}(r)_A, \qquad \Delta c_{\text{unr}} = c_{\text{unr}, B} - c_{\text{unr}, A}$$

If either solution lacks an indicator, its delta in `delta_metrics` is `None` and the summary says "not available"; the flat keys `delta_mean_skill_fit`, `delta_mean_rank` and `delta_unranked_count` then fall back to $0$ (R11).

How to read the signs: a positive $\Delta \bar{\sigma}$ means B has better skill fit. A positive $\Delta \bar{r}$, $\Delta G$, $\Delta \operatorname{Var}(r)$ or $\Delta c_{\text{unr}}$ means B is worse on that indicator. The `trade_off_summary` turns these deltas into plain sentences.

### 4.2 Allocation Diff & Displaced Student Identification
Define how student re-allocations are classified:
- **Changed Assignments:** $\{(s, p_A, p_B) : x_{s, p_A}^{(A)} = 1 \land x_{s, p_B}^{(B)} = 1 \land p_A \ne p_B\}$

  The code walks the students present in both solutions in ascending student ID order and keeps those whose project differs. Each entry records both projects, both stated ranks, both skill-fit scores, `rank_delta` and `rank_change`. A student present in only one solution is not listed. `is_distinct` is true exactly when this set is non-empty, and `changed_students_count` is its size.
- **Worsened Students ($\Delta r_s > 0$):** Students whose preference rank worsened in Solution B.
- **Improved Students ($\Delta r_s < 0$):** Students whose preference rank improved in Solution B.

The rank change of student $s$ is

$$\Delta r_s = r_s^{(B)} - r_s^{(A)}$$

with unranked projects at rank $m + 1$ (R14). The code reads $m$ from the per-project capacity indicators; if neither solution has them, it falls back to the largest stated rank plus one. A student is `WORSENED` if $\Delta r_s > 0$, `IMPROVED` if $\Delta r_s < 0$ and `SAME` if $\Delta r_s = 0$ (for example, a move between two unranked projects). Only changed students are classified, since a student who keeps the same project keeps the same rank. The totals are `rank_improved_count` and `rank_worsened_count`.

---

## 5. Transparent Recommendation Rules

*In accordance with Section 9 of the specification, recommendations must separate calculated evidence from advice across distinct policy priorities.*

`generate_recommendations` in `app/engine/recommendations.py` produces one recommendation per policy priority from the feasible alternatives of a single run. Each recommendation has three parts that the recommendations page shows separately: the criteria used, the calculated evidence (values read from the indicators in §3) and the advice (a sentence on when to adopt the solution). The evidence is computed; the advice is a normative statement written by the team, and the page states that the final decision rests with the programme committee.

Rules common to all three priorities:
- **Choice set:** only the alternatives of the selected run are compared. A recommendation is the best of these alternatives under the stated rule, not a new optimum over all possible allocations.
- **Lexicographic order:** each rule compares the criteria in the listed order; a later criterion only breaks ties in the earlier ones.
- **Ties:** if two alternatives are equal on every criterion, the one with the lowest alternative number is recommended, because the run lists its solutions in that order.
- **Missing indicators:** a missing value counts as the worst possible value, so a solution without indicators is never preferred to one with them.
- **Overlap:** the same alternative can be recommended under more than one priority. That means the trade-off between those priorities is small in this run.
- **No solutions:** an infeasible run has no alternatives, so no recommendation is made; the run page reports the infeasibility instead (§6).

### 5.1 Policy Priority 1: Student Preference Maximization
- **Quantitative Selection Criterion:** lexicographic minimization of the unranked count $c_{\text{unr}}$, then the mean rank $\bar{r}$, then the worst rank $r_{\max}$ (§3.3). No student placed outside their list is the first concern; the average and the worst-off student break ties.
- **Calculated Evidence Reported:** $\bar{r}$, $c_{\text{unr}}$ and $r_{\max}$ of the recommended alternative, plus its mean skill fit $\bar{\sigma}$ (§3.2), so the cost in skill fit is visible next to the gain in preferences.
- **Administrative Advice & Trade-Off Warning:** adopt this alternative when student satisfaction, morale and avoiding appeals come first. It can lower skill fit, because students go where they want rather than where their skills match; the reported $\bar{\sigma}$ and the comparison page (§4) show how much.

### 5.2 Policy Priority 2: Project Delivery & Technical Competence
- **Quantitative Selection Criterion:** lexicographic maximization of the mean skill fit $\bar{\sigma}$, then minimization of the unmet soft requirements count (§3.2). Mandatory requirements are not part of the rule, because every feasible alternative already meets them (R13).
- **Calculated Evidence Reported:** $\bar{\sigma}$ and the unmet soft requirements count of the recommended alternative, plus its mean rank $\bar{r}$, so the cost in student preferences is visible.
- **Administrative Advice & Trade-Off Warning:** adopt this alternative when partner organizations or client deliverables demand strong technical and domain skills. Students may get lower-ranked projects; the reported $\bar{r}$ and the comparison page show how many students move and how far their ranks change.

### 5.3 Policy Priority 3: Balanced & Egalitarian Compromise
- **Quantitative Selection Criterion:** lexicographic minimization of the rank Gini coefficient $G$, then the rank variance $\operatorname{Var}(r)$, then the mean rank $\bar{r}$ (§3.3, R9). There is no composite score and no weight. This rule is separate from the BALANCED solver strategy (§2.5): the strategy generates an alternative by minimizing the worst rank and then maximizing preference and skill fit, while this rule picks among all generated alternatives by how evenly ranks are spread. The criteria shown on the page were corrected in #28 to match the code.
- **Calculated Evidence Reported:** $G$, $\operatorname{Var}(r)$, $\bar{\sigma}$ and $\bar{r}$ of the recommended alternative.
- **Administrative Advice & Trade-Off Warning:** adopt this alternative when the committee wants a fair compromise that avoids extreme individual disadvantage. Equal is not the same as good: if every student got their third choice, $G$ would be $0$. $\bar{r}$ is therefore reported next to $G$, and it should be checked before this alternative is chosen over the one from §5.1.

---

## 6. Assumptions, Boundary Conditions & Edge Cases

The model rests on the assumptions below. Each one is tested; the edge-case numbers refer to `tests/test_edge_cases.py` and `docs/testing_and_quality.md` §3.

1. **Student Submission Incompleteness.** A student may rank fewer than three projects, or none; this gives a warning, not a rejection, because the student must still be placed (R6, edge case 1). An unranked project gets the penalty rank $r_{s,p} = m + 1$ and preference score $\phi_{s,p} = 0$, so any ranked project is better for the solver than any unranked one (R14). The same penalty is used in every rank indicator in §3, so the indicators measure what the solver optimised. In the saved result, the student's `preference_rank` stays empty and the student is counted in `unranked_count`, so the interface never shows a rank the student did not give.

2. **Ties in Preferences.**
   - *Across students:* many students may rank the same project first. This is valid and always solved (edge case 2). Among allocations equal on the strategy's main goal, the secondary term in the objective (§2.5) picks the one that is better on the other goal. Any remaining exact tie is resolved the same way every time, because the model is built in sorted identifier order and HiGHS runs on one thread (R16). The same input therefore gives the same alternatives, which keeps the demonstration reproducible.
   - *Within one student's list:* two projects with the same rank, or the same project listed twice, are rejected before solving, because a rank must say which of two projects the student prefers (R12). A rank below 1 is also rejected.

3. **Skill Levels.** Levels run from 1 to 5; a skill the student does not have counts as level 0. Any other stored level is rejected (R7).
   - A student with no reported skills gets skill fit $\sigma_{s,p} = 0$ on every project with non-mandatory requirements and stays assignable (edge case 3). Such a student can never meet a mandatory requirement.
   - A project with no non-mandatory requirements gives every student $\sigma_{s,p} = 1$, so skill fit does not distinguish between students there (edge case 4).
   - Mandatory requirements are hard constraints and do not count towards skill fit, so they are not counted twice (R4).
   - A mandatory requirement must be met by **at least one** student on the project, not by every student (R13). A project with minimum headcount 0 that stays empty does not need its mandatory skills.
   - A skill missing from the catalogue gives a warning and is added to the catalogue under its own identifier when the cohort is saved (R17, D16).

4. **Feasibility Boundaries.** The allocation is infeasible exactly when no assignment satisfies constraints 1–4 of §2.4 together. Validation finds the clear cases before solving:
   - fewer seats than students: $\sum_p u_p < n$ (edge case 7);
   - more minimum seats than students: $\sum_p l_p > n$ (edge case 8);
   - more students locked to a project than it can take (fixed assignments above $u_p$);
   - no student in the cohort meets a mandatory requirement of some project (edge case 12). This check is stricter than the model in one case, see §7.

   Other conflicts only appear in combination, for example a lock that uses up the only qualified student, or minimum headcounts that leave too few qualified students for another project. These the solver proves infeasible. In both cases the run is saved with status `INFEASIBLE`, no solution, and a message with the reasons; no constraint is relaxed (R2, edge case 13). Input that is wrong rather than impossible (an unknown project ID, a student locked to two projects, invalid levels or ranks) is saved as `INVALID_INPUT` with the errors. When input is both invalid and infeasible, it is reported as invalid, so the user fixes the data first (D16).

### 6.1 Summary of the 15 Edge Cases

The table below summarises how the application handles the 15 edge cases specified in the assignment. Each case is covered by a test in `tests/test_edge_cases.py`.

| Case | Edge case | Application behaviour | Test function |
|---|---|---|---|
| 1 | Incomplete preferences | Accepts the input with a warning and completes the assignment. Unranked projects receive a penalty rank. | `test_edge_case_1_incomplete_preferences` |
| 2 | Identical preferences across students | Allows students to have the same preferences and produces an allocation that respects project capacities. | `test_edge_case_2_tied_preferences_across_students` |
| 3 | Student without skills | Accepts the student and calculates a skill-fit score of 0 for a project with unmet non-mandatory skill requirements. | `test_edge_case_3_zero_skills_student` |
| 4 | Project without skill requirements | Accepts the project and assigns a neutral skill-fit score of 1.0. | `test_edge_case_4_zero_requirements_project` |
| 5 | Unknown project in preferences | Rejects the input and identifies the unknown project. | `test_edge_case_5_unknown_project_in_preferences` |
| 6 | Unknown skill identifiers | Generates warnings identifying skills missing from the catalogue. | `test_edge_case_6_unknown_skill_in_entity` |
| 7 | Insufficient total capacity | Detects that there are more students than available places and reports infeasibility. | `test_edge_case_7_aggregate_capacity_deficit` |
| 8 | Excessive minimum capacity | Detects that the total minimum project capacity exceeds the number of students and reports infeasibility. | `test_edge_case_8_aggregate_min_capacity_excess` |
| 9 | Minimum capacity exceeds maximum | Rejects the invalid project capacity settings. | `test_edge_case_9_capacity_inversion` |
| 10 | Contradictory fixed assignments | Rejects a student being locked to two different projects. | `test_edge_case_10_conflicting_fixed_locks_same_student` |
| 11 | Fixed assignments exceed capacity | Detects that too many students are locked to one project and reports infeasibility. | `test_edge_case_11_fixed_locks_exceeding_project_capacity` |
| 12 | Unavailable mandatory skill | Detects that no student meets a project's mandatory requirement and reports infeasibility. | `test_edge_case_12_unavailable_mandatory_skill` |
| 13 | Infeasible assignment | Returns `INFEASIBLE` and no solutions when the given cohort cannot be allocated. | `test_edge_case_13_no_feasible_solution` |
| 14 | Only one feasible solution | Returns exactly one solution, even when more alternatives were requested. | `test_edge_case_14_single_feasible_solution` |
| 15 | Duplicate alternatives | Uses no-good cuts to generate distinct assignments and stops when no further alternatives exist. | `test_edge_case_15_duplicate_avoidance_no_good_cuts` |

Cases 5–12 mainly test input validation and feasibility checks, while cases 1–4 and 13–15 also demonstrate behaviour of the real assignment engine. The engine-based tests use a temporary SQLite database to ensure that they can run independently.

---

## 7. Limitations & Analytical Deficiencies

1. **Computational Complexity.** ILP is NP-hard in general, so there is no guarantee that solve time grows slowly with the cohort. The model has $n \cdot m$ binary assignment variables and about $n + 2m$ constraints, plus one per fixed assignment, per mandatory requirement and per earlier alternative. For the cohort sizes of one programme it is fast: under 0.4 s per strategy for 300 students and 30 projects (§1.2). Three things would make it slower: many more students and projects, many mandatory requirements that few students meet, and BALANCED, which solves twice. The application has no time limit on the solver, so a very large or very tight cohort would keep the user waiting instead of returning the best allocation found so far.

2. **Linear Preference Assumptions.** The preference objective adds up ranks, so moving one student from 1st to 2nd choice costs the same as moving another from 4th to 5th. Real students probably care much more about the first step, and an unranked project ($m + 1$) is likely worse for a student than one step below their last choice. The BALANCED strategy partly answers this by protecting the worst-off student first, and the Gini coefficient (§3.3) shows how unequal the outcome is, but neither is a model of the students' actual utility. The normalised score $\phi_{s,p}$ (a Borda-type count) has the same linearity. A convex penalty, for example squared ranks, would be a natural next step and would keep the model linear in $x$, since the penalty is computed before solving.

3. **Individual vs. Team Synergies.** Skill fit $\sigma_{s,p}$ is scored per student, against the project's requirements. It does not see the team: three students strong in the same skill score as well as three students who cover different skills, and personal working relations are not modelled at all. Mandatory skills are the only team-level rule (at least one qualified student per project, R13). Modelling complementarity would need variables for pairs of students or coverage per skill, which makes the model larger and harder to explain to a coordinator.

4. **Static Allocation.** Each run is a snapshot. If a student leaves or a project is cancelled during the semester, the coordinator must lock the students who should stay (fixed assignments, R3) and run again; the model has no notion of the cost of moving students who are already working on a project, and it does not plan over time.

5. **Further simplifications we know about.**
   - *SkillFit tie-break:* the preference term in SKILL_FIT has weight $10^{-3}/n$. Because skill-fit totals are not integers, this weight could in principle outweigh a very small difference in skill fit. Strategy 1 does not have this problem (§2.5).
   - *Mandatory-skill pre-check:* validation reports a mandatory requirement that no student meets as infeasible even for a project with minimum headcount 0, which the model itself could leave empty (R13). In that rare case the run is rejected although an allocation without that project exists. The coordinator can remove the requirement or the project and run again.
   - *Self-reported data:* skill levels are reported by the students and not checked, so skill fit is only as good as the reports.
   - *Fixed weights:* the tie-break weights and $\lambda = 0.5$ in BALANCED are set by us, not by the coordinator. The three alternatives and the recommendations (§5) show the trade-off instead of hiding it in one weight, but a coordinator cannot tune the balance in the interface.
