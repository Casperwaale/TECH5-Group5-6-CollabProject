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
- **Victor Goller:** I used Claude Code in VS Code, plus a subagent I set up for the ILP code (`.claude/agents/ilp-agent.md`).

  *What I used it for:*
  - **Working agreement (week 1).** Drafted `AGENTS.md`, the pull request template and `docs/team_b_decisions.md`. The rules live in a plain file, so teammates using other AI tools read the same rules.
  - **Requirements.** Went through the brief, the tests, the schema and the starter code, and listed every rule the model must follow (R1–R17), each with its source.
  - **ILP model.** I made the modelling decisions. AI helped with notation, consistency and the LaTeX version (`docs/model/ilp_formulation.tex`).
  - **`solvers.py`.** Built step by step in the TECH4 order: data, model, solve, read results. One pull request per step. The ILP agent is limited to the TECH4 toolkit and style, and it is not given our model. The code therefore uses constructs I can explain line by line.
  - **Robustness.** A sweep of bad inputs found three bugs: rank gaps after a deleted project, a crash on a skill missing from the catalogue, and the wrong status when input was both invalid and infeasible. Fixed in PR #25 and #26.
  - **Git.** Claude created the branches, wrote the commits in our format, pushed, and opened the pull requests with the template filled in. I am the author of every commit. All 27 of my commits on `main` name Claude in a `Co-Authored-By` line.
  - **Documentation.** Analytical note §1, §2, §6 and §7, the demonstration guide, the architecture diagrams and the first draft of the slides.

  *How I kept control:*
  - The supplied tests are the specification. `AGENTS.md` forbids editing a test to make it pass.
  - 16 of my 18 merged pull requests were approved by a teammate. The other two (#8 and #9) were solver PRs I had let Claude stack on top of each other. They were merged into their base branch instead of `main`. We reopened them against `main` as #12 and #13, both approved, and stopped stacking pull requests.
  - I checked AI output against the sources. Early on it presented requirements as open choices when the brief or the tests already settled them. It also derived one rule from the brief alone that the tests contradict: whether students may be left unassigned. After that we wrote a rule at the top of `team_b_decisions.md`: check every source before calling something a choice, and the tests win conflicts.

  *What I learned:*
  - AI was fast and reliable at routine work: Git, formatting, documentation and consistency checks. It was weaker at knowing what had already been decided, unless it was pointed to the sources.
  - Rules written once in a file worked better than repeating instructions in every prompt.

- [Ole Kristian Skaar: AI use, to be written by Ole Kristian Skaar]
- **Alex Solheim:** I used Claude mainly as a guide for Git and GitHub and as a checking and validating aid for the Team A work. I had little Git experience before this project, so I asked it to take me through each step of the branch, commit, push, pull request and merge flow, and I ran every command myself in the terminal. It also helped improve and polish the Team A notes in `AGENTS.md` (#38) and helped with the Week 2 report and the PDF version of the analytical note. I read every diff before committing, checked the field names in the notes against `compare.html` and `routes.py`, ran `pytest -q` before each commit, and pulled my teammates' branches to my machine to run the tests and the pages before I approved them. I did not let it change the supplied tests, and I checked its claims against the repository.
- **Herman Kilde:** I used Claude Code as a step-by-step guide. Before this project I could write simple Python and SQL, but I had used GitHub very little. It explained the task, the code base and each step of the branch, commit, push, pull request and merge flow, and I ran every Git command myself in the terminal. It also helped a lot with understanding the existing code, how everything was connected and the architecture itself. 
- **Nils Lærum Harloff:** I used Claude Code as a step-by-step guide and as a coding aid. I had used Git and GitHub little before this project, so it took me through each step of the branch, commit, push, pull request and merge flow. It helped me write the comparison page and its tests (#23), remove the xfail markers from the supplied UI tests (#27) and write analytical note §5 (#32), and it checked the Team A part of the Week 2 report against the code. It ran `pytest -q` before each commit, I made it ask for my approval before every push, and I opened all three pull requests myself. I did not let it change the supplied tests to make them pass, and my commits carry a `Co-Authored-By` line naming Claude.

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
- **Alex Solheim:** 
I learned how to work better as a team, not just our self chosen teams, but also across the Development team. Working in a common repository requires solid ground rules which I felt we had in the team contract, as well as smooth and fast communication in our Messenger group. This allowed us to collaborate more seamlessly and without any big issues, which is something that makes group work much more efficient in my experience. I also think the way we split the tasks between the members in Team A was very effective, and especially that we did it from the get go so that each of us had clear objectives which allowed us to take our personal workstreams as far as possible without interfering with the others streams. Lastly, I feel more comfortable with the whole Git flow now, specifically with things like checking the base repository when opening a pull request, because as others also experienced, mine defaulted to the upstream repository.
- **Herman Kilde:** I had used GitHub very little before this project, and my coding experience was limited to simple Python and SQL, so at the start I was unsure how to approach the task. What I take with me most is how empowering AI can be. With Claude as a guide, I was able to take on tasks that I would otherwise have felt were beyond my abilities, and I got to contribute to a real application together with the rest of the team. I also gained a better understanding of how software is built in a team. Working on separate branches and having teammates review each change before it went in felt slow at first, but it made me more confident because I knew someone else would look at my work. I now feel much more comfortable with GitHub and with taking on technical tasks that seem too difficult at first. Additionally, it was exciting to work on a project with a potential real-world application.
- **Nils Lærum Harloff:** I had used Git and GitHub little before this project. The main thing I learned is what each step does: a commit exists only on my machine, a push puts the branch on GitHub, and nothing reaches `main` until a pull request is reviewed and merged. Once I understood that, I could steer the AI instead of just accepting what it did. I also learned to check where a pull request goes every time. Our repository is a fork, so GitHub suggested the instructor's repository by default, and I made that mistake once before I learned to look for the right base repository and the expected number of commits. AI made me much faster, but I am still responsible for what is published under my name, so I set clear limits on what it could do without asking me. Finally, the supplied tests and the working agreement in `AGENTS.md` made it clear when a task was done and what I was allowed to change.
- **Victor Goller:**
  - **A correct model is not yet a working product.** The ILP was right on paper, but a sweep of bad inputs still found three bugs. Handling wrong data and reporting infeasibility clearly needed as much care as the model itself.
  - **Write code I can defend line by line.** I kept the solver to the TECH4 constructs I know, even where shorter Python existed. In a review or a presentation I can explain every line.
  - **Small pull requests, straight to `main`.** One PR per solver step kept each review short. Stacking PRs on top of each other saved no time and caused two wrong merges.
  - **Git and GitHub at a larger scale.** I had used Git before, but never this much: a branch, a pull request and a review for every change. It felt slow at first, but the history now shows who did what and why. I also learned that pull requests from a fork default to the upstream repository, so the target has to be checked every time.
  - **Check documentation against the code, as with tests.** The starter docs described PuLP/CBC and a different architecture, and our own diagrams had to be checked against the real classes. Documentation drifts unless someone checks it.
- **Casper Waale-Andersen:** 
I learned to check the base repository every time I open a pull request: GitHub defaults to the upstream repository (`jcgoez`), and several of our PRs went there by mistake. I also learned not to merge a document that concerns both teams until someone from each team has reviewed it; I merged PR #32 too early. Working in small steps, with one branch and one PR per function, gave us a clean history that makes it easy to see who did what and why. Finally, I got better at prompting Claude Code precisely: pointing it to the requirement IDs and the tests gave much better output than describing the task in general terms.
- [Ole Kristian Skaar: personal lessons, to be written by Ole Kristian Skaar]
