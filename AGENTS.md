# TECH5 Student-to-Project Assignment DSS

Flask decision-support app that assigns students to semester projects and explains the trade-offs between alternative allocations. Two teams build one in-process application:

- **Team A** (visualization & recommendation): `app/visualization/`
- **Team B** (assignment engine): `app/engine/` and `app/domain/validation.py`

The teams communicate only through the contract in `app/contract/contract.py` and the domain objects in `app/domain/models.py`.

## Commands

```bash
python -m venv .venv             # once, to create the project venv
source .venv/bin/activate        # macOS/Linux: always use the project venv
.venv\Scripts\Activate.ps1       # Windows (PowerShell): same, instead of the line above
pip install -r requirements.txt
pytest -q                        # full suite
python run.py                    # app at http://127.0.0.1:5000
python run.py 5001               # macOS: port 5000 is taken by AirPlay Receiver, use another port
```

Test baseline on the starter code: **36 passed, 15 xfailed**. A change must not turn any passing test into a failure. Xfails turning into passes are expected as features land.

## Rules for every session and agent

1. **Shared files need both teams' agreement.** Don't change `app/contract/contract.py`, `app/domain/models.py` or `app/persistence/schema.sql` without approval from one member of each team (Team A and Team B).
2. **Never edit, delete or re-mark a supplied test to make it pass.** Known exception: three tests assert the unimplemented stubs (`test_assignment_engine_initialization`, `test_assignment_engine_raises_not_implemented`, and the `NotImplementedError` checks in `tests/test_contract_and_engine.py`). Change them only once `docs/team_b_decisions.md` records approval.
3. **Never relax a hard constraint to get an answer.** Infeasibility is a valid result: report it with diagnostics.
4. **No unexplained crashes.** Every bad-input path ends in rejection, a warning, an explicitly allowed partial result, or a reported infeasibility.
5. **Stay in your team's area** unless told otherwise:
   - **Team A:** `app/visualization/` (routes, templates, static files) and its tests.
   - **Team B:** `app/engine/`, `app/domain/validation.py` and their tests.
   - **Shared, change only by agreement:** `app/contract/`, `app/domain/models.py`, `app/persistence/`, `AGENTS.md`, `.github/`.
6. **Follow the git workflow below.** Never commit directly to `main`.

## Git workflow

The brief grades our Git history, our reviews and how we use AI, so every change follows the same steps, whoever or whatever made it.

1. **Start from the latest `main`:** `git pull` on `main` before creating a branch.
2. **One branch per task**, named `<area>/<short-topic>`: `team-a/...`, `team-b/...`, or `setup/...` for shared tooling. Examples: `team-b/metrics`, `team-a/compare-view`.
3. **Small commits**, one logical change each. Message format:
   ```
   <area>: <what changed, imperative, max ~70 characters>

   <why: the reason, and decision IDs such as D8 where relevant>

   Assisted-by: <AI tool>   (only if AI helped; one line per tool)
   ```
   `<area>` is e.g. `engine`, `validation`, `ui`, `tests`, `docs`, `setup`. A `Co-Authored-By:` line added by an AI tool also counts as disclosure.
4. **Open a pull request** into `main` and fill in every section of `.github/pull_request_template.md`. Agents opening pull requests must do this too. Use a **draft** pull request while work is still in progress.
5. **Review before merging.** At least one person other than the author approves. Changes to shared files need an approval from someone on each team. Reviewers leave at least one concrete comment or question, not just an approval.
6. **Merge, then delete the branch.** Everyone pulls `main` regularly.

## Team A notes

*To be written by Team A: conventions for routes and templates, and what the UI needs from the engine.*

## Team B notes

- **Read `docs/team_b_decisions.md` before any engine work.** It records the modelling and policy decisions. If a task needs a decision that isn't there, stop and ask; don't choose silently.
- **The tests are the spec.** `tests/test_metrics.py`, `tests/test_solvers.py` and `tests/test_edge_cases.py` define the expected behaviour exactly.
- **Indicator keys are consumed by other code.** `app/engine/recommendations.py` and the templates read keys such as `fairness.mean_rank`, `fairness.worst_rank`, `fairness.unranked_count`, `fairness.rank_gini`, `fairness.rank_variance`, `efficiency.mean_skill_fit`, `efficiency.unmet_soft_requirements_count` and `capacity.overall_utilization_pct`. Keep them stable.
- **`app/contract/mocks.py` shows output shape only.** Its numbers are synthetic, and it maps unranked projects to rank 1. Don't copy its logic.
- **Strategy keys sent by the UI:** `PREFERENCE`, `SKILL_FIT`, `BALANCED`. The UI requests 1–4 alternatives.
- **Persistence:** `self.run_repo.save_run(run)`. Foreign keys are enforced, so every `Assignment.project_id` must be a real project.

## Code style

Match the existing code: type hints, Google-style docstrings, module imports (`from app.domain import models`), and dataclasses for domain objects.
