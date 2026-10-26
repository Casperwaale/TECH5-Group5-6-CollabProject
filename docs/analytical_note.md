# Deliverable 6: Analytical Note & Mathematical Formulation
## Student Submission Template — TECH5 Collaborative Project

**Team:** Group 5-6  
**Authors (Team B - Assignment Engine):** Victor Goller, Casper Waale, Ole Kristian Skaar  
**Authors (Team A - Visualization & Recommender):** Alex Solheim, Herman Kilde, Nils Lærum Harloff  
**Course:** TECH5 Programming & Application Design, NHH Norwegian School of Economics  
**Date:** [Submission Date]

---

> [!IMPORTANT]
> **Instructions for Students:**  
> This document serves as the formal deliverable template for **Deliverable 6 (Analytical Note)** as defined in Section 15 and Section 6 of the TECH5 project specification (`projectTech5.tex`).  
>
> Replace all bracketed text `[...]` with your team's mathematical formulation, indicator derivations, decision criteria, and critical reflections. Maintain rigorous mathematical notation and explain how your analytical design translates directly into your Python implementation in `app/engine/solvers.py` and `app/engine/metrics.py`.

---

## 1. Problem Definition & Mathematical Modeling Approach

### 1.1 Business Context & Decision Dilemma
*Describe the real-world allocation challenge faced by academic coordinators. Discuss the inherent conflict between collective project quality (skill matching) and individual student satisfaction (preference rank).*

[Provide a 1–2 paragraph summary of the problem, referencing Rezaeinia et al. (2022) for context without copying their proprietary algorithm.]

### 1.2 Chosen Assignment Methodology & Academic Justification
*Identify your approved assignment methodology (e.g., Integer Linear Programming with PuLP/CBC, stable matching variant, heuristic search, or bipartite min-cost flow).*

[State your chosen method, explain why it is appropriate for this problem scale, and justify its computational feasibility within a single-process Python application.]

---

## 2. Mathematical Formulation

> **Draft by Team B for review.** One model with three objective functions: the sets, parameters, variables and constraints (§2.1–2.4) are shared by all strategies; only the objective (§2.5) changes. Rules tagged R1–R17 refer to the requirements in `docs/team_b_decisions.md`, each traced to the brief, the tests, the schema or the starter docs. The objective functions in §2.5 are our own design choice and are marked **proposal**.

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
\text{stated rank of } p \text{ by } s, & \text{if } s \text{ ranked } p,\\
m + 1, & \text{otherwise.}
\end{cases}
$$

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

- **Strategy 1: PREFERENCE (minimise total rank)** (proposal)

$$
\min \; Z_{\text{pref}} = \sum_{s \in S} \sum_{p \in P} r_{s,p} \, x_{s,p} \;-\; \varepsilon_{\text{pref}} \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \, x_{s,p},
\qquad \varepsilon_{\text{pref}} = \frac{1}{n + 1}
$$

The rank sum is an integer, and the skill term is at most $n \, \varepsilon_{\text{pref}} < 1$, so it can only break ties: it never makes the rank sum worse. Minimising the rank sum equals minimising the mean rank $\bar{r}$ reported by the indicators.

- **Strategy 2: SKILL_FIT (maximise total skill fit)** (proposal)

$$
\max \; Z_{\text{skill}} = \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \, x_{s,p} \;+\; \varepsilon_{\text{skill}} \sum_{s \in S} \sum_{p \in P} \phi_{s,p} \, x_{s,p},
\qquad \varepsilon_{\text{skill}} = 10^{-3} / n
$$

The preference term is at most $10^{-3}$, so it breaks ties between solutions with (practically) equal skill fit. Unlike Strategy 1 this is not an exact guarantee, because skill-fit totals are not integers; we state this as a limitation.

- **Strategy 3: BALANCED (protect the worst-off, then balance)** (proposal). Solved in two stages, so no weight between fairness and efficiency has to be tuned:

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

**Open for Team B review:** the form of each objective, $\lambda = 0.5$, and whether BALANCED should use the two-stage form or a single weighted objective.

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

### 5.1 Policy Priority 1: Student Preference Maximization
- **Quantitative Selection Criterion:** [e.g., Lexicographic minimization of unranked count, then $\bar{r}$, then $r_{\max}$]
- **Calculated Evidence Reported:** [List indicators presented to the user]
- **Administrative Advice & Trade-Off Warning:** [When to apply and what compromises are made]

### 5.2 Policy Priority 2: Project Delivery & Technical Competence
- **Quantitative Selection Criterion:** [e.g., Maximization of mean skill fit $\bar{\sigma}$]
- **Calculated Evidence Reported:** [List indicators presented to the user]
- **Administrative Advice & Trade-Off Warning:** [When to apply and what compromises are made]

### 5.3 Policy Priority 3: Balanced & Egalitarian Compromise
- **Quantitative Selection Criterion:** [e.g., Multi-objective composite score or Gini minimization]
- **Calculated Evidence Reported:** [List indicators presented to the user]
- **Administrative Advice & Trade-Off Warning:** [When to apply and what compromises are made]

---

## 6. Assumptions, Boundary Conditions & Edge Cases

Document all operational assumptions:
1. **Student Submission Incompleteness:** How unranked projects are penalized.
2. **Ties in Preferences:** How students with identical preference lists are handled.
3. **Skill Levels:** Handling students with zero declared skills or projects with zero requirements.
4. **Feasibility Boundaries:** Exact conditions under which the problem is proved mathematically infeasible.

---

## 7. Limitations & Analytical Deficiencies

Critically reflect on the limitations of your analytical model:
1. **Computational Complexity:** Scalability limits as $|S|$ and $|P|$ grow.
2. **Linear Preference Assumptions:** Limitations of Borda count vs. non-linear student utilities.
3. **Individual vs. Team Synergies:** Individual skill evaluation vs. collective team diversity.
4. **Static Allocation:** Inability to capture dynamic scheduling or mid-semester changes.
