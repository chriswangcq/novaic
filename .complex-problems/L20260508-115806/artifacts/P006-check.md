# P006 success check

## Summary

P006 is solved. Required runtime worker roles are now explicit in production startup and deploy status. The system no longer accepts a vague worker aggregate as sufficient evidence for role-level worker health.

## Evidence

- Result: `R018`
- Syntax:
  - `bash -n scripts/start.sh`
  - `bash -n deploy`
- Guardrails:
  - `python3 scripts/ci/lint_runtime_worker_supervision.py`
  - `python3 scripts/ci/lint_deploy_fresh_smoke.py`
  - `python3 scripts/ci/check_start_config_contract.py`
  - `python3 scripts/ci/lint_docs_status_consistency.py`
  - `./scripts/ci/lint_current_docs_residue.sh`
  - `git diff --check -- deploy scripts/start.sh docs/runbooks/deploy.md scripts/ci/lint_runtime_worker_supervision.py scripts/ci/lint_deploy_fresh_smoke.py .github/workflows/lint.yml`
  - `python3 -m py_compile scripts/ci/lint_runtime_worker_supervision.py scripts/ci/lint_deploy_fresh_smoke.py`
- Residue scan:
  - `rg -n "worker_count|Workers:|subscriber-\\*\\.log" deploy scripts/start.sh docs/runbooks/deploy.md scripts/ci/lint_runtime_worker_supervision.py`
  - Only intentional guard references remain inside the lint script.

## Criteria Map

- `start.sh` verifies exact worker/subscriber counts: satisfied by `verify_runtime_processes`.
- Startup exits non-zero on wrong role count: satisfied by `Required runtime subprocess supervision failed.` path.
- `deploy status` role-level table: satisfied by `check_role` table.
- CI/lint coverage: satisfied by `scripts/ci/lint_runtime_worker_supervision.py` and workflow wiring.
- Documentation: satisfied by `docs/runbooks/deploy.md`.

## Execution Map

- Ticket `T019` was classified `one_go`.
- Execution result `R018` records start/status supervision, docs, CI guard, and local verification.
- This check accepts `R018` as complete for P006.

## Stress Test

- Removing `verify_runtime_processes` fails lint.
- Removing any required role from `start.sh` or `deploy status` fails lint.
- Reintroducing the old coarse `worker_count` status fails lint.
- Leaving the wrong `subscriber-*.log` operator hint would be caught by the residue scan evidence.

## Residual Risk

- Shell supervision proves required subprocess shape. It does not replace semantic queue/FSM correctness tests; those remain in the runtime code and final residue verification problem.
