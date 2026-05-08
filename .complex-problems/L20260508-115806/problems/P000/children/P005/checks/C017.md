# P005 success check

## Summary

P005 is solved. Deploy restart is no longer verified only by stale tail/process evidence: restart captures a remote epoch, runs fresh-log smoke after startup, and exposes the same timestamp-aware check as `./deploy fresh-smoke [epoch]`. CI now guards the deploy hook, command, critical logs, docs, and workflow wiring.

## Evidence

- Result: `R017`
- Syntax:
  - `bash -n deploy`
  - `bash -n scripts/start.sh`
- Guardrails:
  - `python3 scripts/ci/lint_deploy_fresh_smoke.py`
  - `python3 scripts/ci/check_start_config_contract.py`
  - `python3 scripts/ci/lint_docs_status_consistency.py`
  - `./scripts/ci/lint_current_docs_residue.sh`
  - `python3 scripts/ci/lint_roadmap_ticket_archaeology.py`
  - `git diff --check -- deploy docs/runbooks/deploy.md scripts/ci/lint_deploy_fresh_smoke.py .github/workflows/lint.yml`
  - `python3 -m py_compile scripts/ci/lint_deploy_fresh_smoke.py`
- UX smoke:
  - `./deploy __help_smoke__ | sed -n '1,80p'`

## Criteria Map

- Restart captures timestamp and verifies fresh logs: satisfied by `remote_epoch`, `restart_all`, and `verify_fresh_backend_logs "$smoke_since"`.
- Manual fresh smoke: satisfied by `fresh-smoke) verify_fresh_backend_logs "${2:-}"`.
- Stable server paths and timestamp evidence: satisfied by remote `/opt/novaic/data/logs` plus `stat -c %Y` mtime checks.
- CI/lint guard: satisfied by `scripts/ci/lint_deploy_fresh_smoke.py` and workflow wiring.
- Documentation: satisfied by `docs/runbooks/deploy.md` fresh-smoke section.

## Execution Map

- Ticket `T018` was classified `one_go`.
- Execution result `R017` records deploy, docs, and CI changes plus local verification.
- This check accepts `R017` as complete for P005.

## Stress Test

- If `restart_all` loses the timestamp capture, lint fails.
- If the post-restart smoke call is removed, lint fails.
- If a critical log is removed from the smoke list, lint fails.
- If docs stop mentioning timestamp-aware fresh smoke, lint fails.
- If someone tries to reuse old `/tmp/novaic-cortex-sandbox-*` style stale path thinking, this change is unaffected because it verifies fixed remote production log paths.

## Residual Risk

- The smoke verifies timestamp freshness of critical logs, not full semantic worker health. That is intentionally covered by the separate runtime worker supervision problem.
