# Runtime worker supervision result

## Summary

Implemented explicit runtime worker supervision in the production start/status path. The backend start script now verifies the exact required worker/subscriber role roster after launch and fails startup on missing or duplicate required subprocesses. Deploy status now reports role-level expected/actual counts.

## Done

- Added `process_count`, `require_process_count`, and `verify_runtime_processes` to `scripts/start.sh`.
- `scripts/start.sh` now verifies exact counts for:
  - `task-worker control`: 2
  - `task-worker execution`: 2
  - `saga-worker`: 2
  - `session-outbox-worker`: 1
  - `saga-outbox-worker`: 1
  - `health`: 1
  - `scheduler`: 1
  - `subscriber`: 1
- Startup exits non-zero with `Required runtime subprocess supervision failed.` if the roster is wrong.
- Fixed the subscriber startup log message to point to `subscriber.log`.
- Replaced the coarse worker total in `deploy status` with a role-level expected/actual table.
- Added `scripts/ci/lint_runtime_worker_supervision.py` to guard start/status roster supervision.
- Wired the new lint into `.github/workflows/lint.yml`.
- Documented required runtime subprocesses in `docs/runbooks/deploy.md`.

## Verification

- `bash -n scripts/start.sh`
- `bash -n deploy`
- `python3 scripts/ci/lint_runtime_worker_supervision.py`
- `python3 scripts/ci/lint_deploy_fresh_smoke.py`
- `python3 scripts/ci/check_start_config_contract.py`
- `python3 scripts/ci/lint_docs_status_consistency.py`
- `./scripts/ci/lint_current_docs_residue.sh`
- `git diff --check -- deploy scripts/start.sh docs/runbooks/deploy.md scripts/ci/lint_runtime_worker_supervision.py scripts/ci/lint_deploy_fresh_smoke.py .github/workflows/lint.yml`
- `python3 -m py_compile scripts/ci/lint_runtime_worker_supervision.py scripts/ci/lint_deploy_fresh_smoke.py`
- `rg -n "worker_count|Workers:|subscriber-\\*\\.log" deploy scripts/start.sh docs/runbooks/deploy.md scripts/ci/lint_runtime_worker_supervision.py`

## Known Gaps

- This verifies process role roster at startup/status. Deeper semantic worker health remains owned by worker code and queue/FSM tests, not shell supervision.

## Artifacts

- `scripts/start.sh`
- `deploy`
- `scripts/ci/lint_runtime_worker_supervision.py`
- `.github/workflows/lint.yml`
- `docs/runbooks/deploy.md`
