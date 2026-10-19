# Deliverable 6: Analytical Note & Mathematical Formulation
## Student Submission Template — TECH5 Collaborative Project

**Team:** Group 5-6  
**Authors (Team B - Assignment Engine):** Victor Goller, Casper Waale  
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
- $K$: catalogued skills.
- $F \subseteq S \times P$: fixed assignments (administrative locks).
- $K_p^{\text{soft}} \subseteq K$: non-mandatory skill requirements of project $p$.
- $M_p \subseteq K$: mandatory skill requirements of project $p$.
- $Q_{p,k} = \{ s \in S : \ell_{s,k} \ge q_{p,k} \}$: students qualified for mandatory requirement $k \in M_p$.
- $P^{M} = \{ p \in P : M_p \neq \emptyset \}$: projects with at least one mandatory requirement.
- $\Sigma = (\text{PREFERENCE}, \text{SKILL\_FIT}, \text{BALANCED})$: the strategies.

All sets are built in sorted identifier order, so the same input always produces the same model (R16).

### 2.2 Model Parameters
- $l_p \in \mathbb{Z}_{\ge 0}$, $u_p \in \mathbb{Z}_{\ge 1}$: minimum and maximum headcount of project $p$, $l_p \le u_p$.
- $\ell_{s,k} \in \{0, 1, \dots, 5\}$: proficiency of student $s$ in skill $k$; $0$ means the skill is not held (R7).
- $q_{p,k} \in \{1, \dots, 5\}$: minimum level that project $p$ requires in skill $k$ (R7).
- $R = m + 1$: penalty rank for an unranked project (R14).
- $r_{s,p}$: preference rank of student $s$ for project $p$ (R14):

$$
r_{s,p} =
\begin{cases}
\text{stated rank of } p \text{ by } s, & \text{if } s \text{ ranked } p,\\
R = m + 1, & \text{otherwise.}
\end{cases}
$$

- $\rho_{s,p} \in [0, 1]$: normalised preference score, $1$ for a first choice and $0$ for an unranked project:

$$
\rho_{s,p} = \frac{R - r_{s,p}}{R - 1}
$$

- $\sigma_{s,p} \in [0, 1]$: skill fit of student $s$ on project $p$, over the non-mandatory requirements only (R4):

$$
\sigma_{s,p} =
\begin{cases}
\dfrac{1}{\lvert K_p^{\text{soft}} \rvert} \displaystyle\sum_{k \in K_p^{\text{soft}}} \min\!\left(1, \frac{\ell_{s,k}}{q_{p,k}}\right), & K_p^{\text{soft}} \neq \emptyset,\\[2ex]
1, & K_p^{\text{soft}} = \emptyset.
\end{cases}
$$

### 2.3 Decision Variables
- $x_{s,p} \in \{0, 1\}$: $1$ if student $s$ is assigned to project $p$.
- $y_p \in \{0, 1\}$ for $p \in P^{M}$: $1$ if project $p$ is used (has at least one student). Needed only so that a project with $l_p = 0$ and a mandatory requirement may stay empty (R13).
- $z \in \mathbb{R}_{\ge 0}$: worst assigned rank, used only by the BALANCED strategy.

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
\sum_{s \in Q_{p,k}} x_{s,p} \ge y_p \qquad \forall p \in P^{M},\ k \in M_p
$$

$$
\sum_{s \in S} x_{s,p} \le u_p \, y_p \qquad \forall p \in P^{M}
$$

The second line forces $y_p = 1$ whenever the project has a student. If $l_p \ge 1$, constraint 2 already makes the project non-empty, so $y_p = 1$ and the requirement must be met.

5. **Distinct alternatives: no-good cuts** (R5). Let $A^{(j)} = \{ (s, p) : x^{(j)}_{s,p} = 1 \}$ be the $j$-th solution found. Before solving for alternative $k$, add for every earlier solution:

$$
\sum_{(s, p) \in A^{(j)}} x_{s,p} \le n - 1 \qquad j = 1, \dots, k - 1
$$

At least one student must then move. If the model becomes infeasible, no further distinct alternative exists; the run returns the solutions found so far and reports their number in `diagnostics["distinct_alternatives"]` (R5).

### 2.5 Optimization Objectives & Strategies

**Order of strategies (R15).** Alternative 1 uses the strategy the user selects. Each next alternative uses the next strategy in $\Sigma$, wrapping around, and adds the no-good cuts above. With PREFERENCE selected and $K = 3$: alternative 1 = PREFERENCE, 2 = SKILL_FIT, 3 = BALANCED.

**Ties (R16).** Each strategy has a secondary term with a small weight, so that among solutions equal on the main goal the one that is better on the other goal is chosen (`docs/testing_and_quality.md`, edge case 2). Any remaining exact tie is resolved by the fixed sorted model order and a single-threaded HiGHS run, so the same input gives the same result.

- **Strategy 1: PREFERENCE (minimise total rank)** (proposal)

$$
\min \; Z_{\text{pref}} = \sum_{s \in S} \sum_{p \in P} r_{s,p} \, x_{s,p} \;-\; \delta \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \, x_{s,p},
\qquad \delta = \frac{1}{n + 1}
$$

The rank sum is an integer, and the skill term is at most $n \delta < 1$, so it can only break ties: it never makes the rank sum worse. Minimising the rank sum equals minimising the mean rank $\bar{r}$ reported by the indicators.

- **Strategy 2: SKILL_FIT (maximise total skill fit)** (proposal)

$$
\max \; Z_{\text{skill}} = \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \, x_{s,p} \;+\; \varepsilon \sum_{s \in S} \sum_{p \in P} \rho_{s,p} \, x_{s,p},
\qquad \varepsilon = 10^{-3} / n
$$

The preference term is at most $10^{-3}$, so it breaks ties between solutions with (practically) equal skill fit. Unlike Strategy 1 this is not an exact guarantee, because skill-fit totals are not integers; we state this as a limitation.

- **Strategy 3: BALANCED (protect the worst-off, then balance)** (proposal). Solved in two stages, so no weight between fairness and efficiency has to be tuned:

  *Stage 1 (egalitarian):* minimise the worst assigned rank

$$
z^{*} = \min \; z \quad \text{s.t.} \quad z \ge \sum_{p \in P} r_{s,p} \, x_{s,p} \quad \forall s \in S, \quad \text{and constraints 1–5}
$$

  *Stage 2 (balance):* among solutions with that worst rank, maximise an equal mix of preference and skill fit

$$
\max \; Z_{\text{bal}} = \sum_{s \in S} \sum_{p \in P} \bigl( w \, \rho_{s,p} + (1 - w) \, \sigma_{s,p} \bigr) x_{s,p}
\quad \text{s.t.} \quad \sum_{p \in P} r_{s,p} \, x_{s,p} \le z^{*} \;\; \forall s \in S, \quad \text{constraints 1–5}, \quad w = 0.5
$$

Both terms lie in $[0, 1]$ per student, so $w = 0.5$ weighs them equally. Stage 1 matches the strategy's label in the UI ("Egalitarian Fairness"): nobody gets a worse rank than necessary.

**Open for Team B review:** the form of each objective, $w = 0.5$, and whether BALANCED should use the two-stage form or a single weighted objective.

---

## 3. Evaluation Indicators & Analytical Metrics

Define the mathematical formulation for all evaluation metrics implemented in `app/engine/metrics.py`:

### 3.1 Feasibility Indicators
- Allocation completeness: $\sum_{s \in S} \sum_{p \in P} x_{s,p} = |S|$
- Capacity compliance check for all $p \in P$
- Fixed lock adherence check
- Mandatory requirement fulfillment count

### 3.2 Efficiency Indicators
- **Mean Skill-Fit Score ($\bar{\sigma}$):**
  $$\bar{\sigma} = \frac{1}{|S|} \sum_{s \in S} \sum_{p \in P} \sigma_{s,p} \cdot x_{s,p}$$
- **Mean Preference Rank ($\bar{r}$):**
  $$\bar{r} = \frac{1}{|S|} \sum_{s \in S} \sum_{p \in P} r_{s,p} \cdot x_{s,p}$$

### 3.3 Fairness Indicators
*Section 6.3 of the specification mandates: rank distribution, unranked count, worst assigned rank, and ONE proposed and justified fairness indicator.*

1. **Rank Distribution:** Histogram vector $[c_1, c_2, \dots, c_{|P|}, c_{\text{unranked}}]$ where $c_k$ is the number of students assigned to their $k$-th choice.
2. **Unranked Allocation Count ($U$):** Count of students allocated outside their submitted preference list.
3. **Worst Assigned Rank ($r_{\max}$):**
   $$r_{\max} = \max_{(s,p) : x_{s,p}=1} r_{s,p}$$
4. **Team's Proposed Fairness Indicator (e.g., Gini Coefficient or Rank Variance):**
   *Provide the mathematical formula, justification, and interpretation:*
   $$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |r_i - r_j|}{2 n \sum_{i=1}^n r_i}$$
   *[Explain why this metric captures inequality among student outcomes]*

### 3.4 Capacity Utilization Metrics
- Per-project utilization percentage:
  $$\text{Util}_p = \frac{\sum_{s \in S} x_{s,p}}{u_p} \times 100\%$$
- Aggregate cohort capacity slack and tightness

---

## 4. Trade-Off Analysis & Solution Comparison

### 4.1 Comparative Delta Formulation
Explain how the system computes performance deltas between Solution A and Solution B:
$$\Delta \bar{\sigma} = \bar{\sigma}_B - \bar{\sigma}_A$$
$$\Delta \bar{r} = \bar{r}_B - \bar{r}_A$$
$$\Delta r_{\max} = r_{\max, B} - r_{\max, A}$$
$$\Delta G = G_B - G_A$$

### 4.2 Allocation Diff & Displaced Student Identification
Define how student re-allocations are classified:
- **Changed Assignments:** $\{(s, p_A, p_B) : x_{s, p_A}^{(A)} = 1 \land x_{s, p_B}^{(B)} = 1 \land p_A \ne p_B\}$
- **Worsened Students ($\Delta r_s > 0$):** Students whose preference rank worsened in Solution B.
- **Improved Students ($\Delta r_s < 0$):** Students whose preference rank improved in Solution B.

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
