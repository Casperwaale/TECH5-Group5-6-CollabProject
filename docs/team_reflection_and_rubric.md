# TECH5 Collaborative Project: Team Reflection, SDLC & Rubric Assessment

Group 5-6. All pull request (PR) numbers and dates are from `git log` on `main`.

## 1. Collaborative Development & Component Division

### 1.1 Team A: Visualization and Recommendation Component
Area: `app/visualization/` and its tests.

- **Alex Solheim:** skill creation and deletion (#15); Team A notes in `AGENTS.md` (#38).
- **Herman Kilde:** project create, edit and delete, with one shared form validator `_parse_project_form` (#24); fixed the criteria listed for the balanced recommendation so they match the code (#28).
- **Nils Lærum Harloff:** side-by-side comparison page with Team A tests (#23); removed the xfail markers from the supplied UI tests (#27); analytical note §5, recommendation rules (#32).

### 1.2 Team B: Assignment Engine
Area: `app/engine/`, `app/domain/validation.py` and their tests.

- **Victor Goller (solver):** working agreement and decisions file (#1); ILP formulation in LaTeX and PDF (#2); setup for Windows and an ILP agent for Claude Code (#3, #4); the solver in small steps: `prepare_data` (#6), `build_model` (#12), `solve_model` (#13), the three strategies (#10) and `execute_run` with the alternatives loop (#11); validation fixes (#25); robustness fixes and decision D16 (#26); infeasibility reasons shown once (#29); analytical note §1, §2, §6, §7 and fixes (#30, #36); demonstration guide (#31); architecture doc and diagrams (#39, #40).
- **Casper Waale-Andersen (metrics):** Pyomo and highspy dependencies (#5); skill fit (#16), Gini (#17), solution comparison (#18) and all solution indicators (#19); analytical note §3–4 (#20); recorded the instructor approval Q1 and decisions D14 and D15 (#21).
- **Ole Kristian Skaar (validation and tests):** input validation checks and tests (#7); rejection of duplicate project preferences (#14); activated the solver tests with temporary test databases (#22); Week 3 update of the analytical note and testing documentation, including the edge-case table (#33).

### 1.3 Contract-First In-Process Collaboration Protocol
The teams talk only through `app/contract/contract.py` (`AssignmentEngineContract`) and the domain objects in `app/domain/models.py`. Both run in one Flask process. Changing a shared file (contract, models, `schema.sql`) needs approval from one member of each team. In practice none of the three shared files was changed after the starter commit: the supplied contract was enough for both teams.

---

## 2. Software Development Lifecycle (SDLC) & AI Pair Programming

### 2.1 SDLC Methodology
We worked in small tasks, each on its own branch and pull request, with the supplied tests as the specification. Week boundaries below are taken from commit dates.

- **Week 1 (13–21 Oct): rules and model.** The starter package arrived on 14 Oct. Victor proposed a shared working agreement on 15 Oct and audited every Team B choice against the brief, the tests, the schema and the starter docs, which split them into requirements (R1–R17) and real decisions (D). Casper proposed Pyomo + HiGHS, Victor agreed (D1, 19 Oct). Victor drafted the ILP model. Ole wrote the first validation checks.
- **Week 2 (22–27 Oct): build.** The instructor approved the method on 22 Oct (Q1). Team B merged the solver (#6, #10–#13), validation (#7, #14, #25), metrics (#16–#19) and activated tests (#22). Team A merged skills (#15), the compare view (#23) and projects (#24), and activated the UI tests (#27). D16 was decided on 27 Oct for the Week 2 deadline, after a cross-check of the solver against the metrics and a bad-input sweep (#26).
- **Week 3 (28 Oct–2 Nov): documentation and polish.** Analytical note sections from both teams (#20, #30, #32, #33, #36), demonstration guide (#31), recommendation criteria fix (#28), architecture doc and diagrams (#39, #40) and Team A notes in `AGENTS.md` (#38).

### 2.2 Communication
- **`AGENTS.md`** is the working agreement for people and AI agents alike: who owns which files, the shared-file approval rule, the Git workflow, and the output keys each team relies on. Each team wrote its own notes section.
- **`docs/team_b_decisions.md`** is the single record of Team B's modelling rules. Each item cites its source; each decision has a status, an owner and a date, and a log at the bottom. Agents must read it before engine work and stop and ask if a decision is missing.
- **Instructor approval (Q1):** the brief requires approval of the method before it becomes the baseline. Professor Julio Goez approved ILP with Pyomo + highspy, including the per-project mandatory-skill rule R13, on 22 Oct.

### 2.3 Git Workflow
- One branch per task named `<area>/<topic>` (`team-a/...`, `team-b/...`, `setup/...`), one PR per branch filled in from `.github/pull_request_template.md`, review by someone other than the author before merge, and a protected `main`. 35 PRs were merged between 20 Oct and 2 Nov.
- Usually someone other than the author merged: Casper merged Victor's solver PRs and Victor merged Casper's metrics PRs. Four Team A PRs (#15, #23, #27, #38) were merged by their own author.
- **Problems.** Several PRs opened against the upstream starter repository (`jcgoez`) by default instead of our fork. PR #32 was merged before it had been reviewed. Some early commits do not follow the `<area>: <message>` format.

### 2.4 AI-Supported Development
`AGENTS.md` requires AI help to be disclosed in each commit. Commits by Victor, Casper, Alex, Herman and Nils carry `Assisted-by:` or `Co-Authored-By:` lines naming Claude.

- **Casper Waale-Andersen:** I used Claude Code for the metrics work (#16–#19). I gave it one function per prompt and pointed it at the rules it had to follow: the requirement IDs in `team_b_decisions.md` (R4 skill fit, R9 Gini, R11 output keys, R14 unranked rank) and the supplied tests as the specification. I read every diff before committing, checked it against the decision it cited, and ran `pytest -q` before each commit. The AI-assisted commits carry a `Co-Authored-By` line (for example 5fefbbb, a43548b, 93f13c1, dedd3ec), and their messages name the requirement they implement.
- [Victor Goller: AI use, to be written by Victor Goller]
- [Ole Kristian Skaar: AI use, to be written by Ole Kristian Skaar]
- [Alex Solheim: AI use, to be written by Alex Solheim]
- [Herman Kilde: AI use, to be written by Herman Kilde]
- [Nils Lærum Harloff: AI use, to be written by Nils Lærum Harloff]

---

## 3. Self-Assessment against the 100-Point Grading Rubric

| Category | Weight | Assessment |
|---|:---:|---|
| **1. Business requirements and analytical formulation** | 10% | Every rule is traced to the brief, tests, schema or starter docs (R1–R17), and the ILP model, indicators, recommendation rules and limitations are written out in `docs/analytical_note.md` and `docs/model/ilp_formulation.tex`. |
| **2. Object-oriented architecture and Python implementation** | 15% | We kept the starter's structure and filled in the strategy pattern with three solver classes over one shared model; the only interface change was the strategy method's arguments (D14). |
| **3. Relational database design and SQL integration** | 15% | We used the supplied schema unchanged, so our own database work is limited to working within its constraints (for example D16 for uncatalogued skills and temporary databases in tests). |
| **4. Assignment Engine functionality and analytical quality** | 20% | The engine never relaxes a hard constraint, proves when no further distinct alternative exists, and reports infeasibility with reasons; known gaps are no solver time limit and an inexact tie-break in SKILL_FIT (note §7). |
| **5. Visualization, recommendations, and interaction** | 15% | Team A built skill and project management and the comparison page on top of the starter UI, and corrected the recommendation criteria so the page shows what the code uses. |
| **6. Component contract and end-to-end integration** | 10% | The real engine replaced the stubs without any change to the contract or domain objects, and the full test suite passes against it. |
| **7. Testing, error handling, and robustness** | 10% | All 75 tests pass with no xfail left, all 15 edge cases have a test, and a bad-input sweep led to the D16 fixes. |
| **8. Git collaboration, SDLC practice, and team process** | 5% | One branch and one reviewed PR per task worked well overall, but PR #32 was merged before review and several PRs first went to the upstream repository. |

---

## 4. Key Lessons Learned & Future Extensions

1. **Refactoring the tests along with the code.** Some supplied tests asserted that the engine was still a stub. When the stubs were replaced, we rewrote those checks to test the real behaviour (R8, recorded before any test was changed) and removed the xfail markers as each feature landed (#16–#19, #22, #27). Writing the rule down first kept the test changes honest.
2. **The contract made parallel work possible.** Team A built the pages against `MockAssignmentEngine` while Team B built the real engine. When the engine was ready, nothing in the contract or the domain objects had to change.
3. **Cross-checking components finds bugs that unit tests miss.** Comparing the solver with the metrics code found that rank gaps after a project deletion made the two disagree, and a bad-input sweep found a crash on uncatalogued skills (D16).
4. **Writing decisions down saves arguments later.** Auditing every choice against all sources turned most "decisions" into requirements we could cite, and the few real decisions have an owner and a date.
5. **Process slips happen under deadline.** Merging #32 before review and PRs going to the upstream repository show that the workflow needs checking on every PR, not just agreeing on once.

Personal lessons:
- [Alex Solheim: personal lessons, to be written by Alex Solheim]
- [Herman Kilde: personal lessons, to be written by Herman Kilde]
- [Nils Lærum Harloff: personal lessons, to be written by Nils Lærum Harloff]
- [Victor Goller: personal lessons, to be written by Victor Goller]
- [Casper Waale-Andersen: personal lessons, to be written by Casper Waale-Andersen]
- [Ole Kristian Skaar: personal lessons, to be written by Ole Kristian Skaar]
