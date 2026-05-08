# Timestamp-aware deploy smoke result

## Summary

Implemented timestamp-aware deploy smoke for backend restarts. The deploy path now captures a remote epoch before `start.sh` restart, then verifies critical backend logs were modified after that timestamp. A manual `fresh-smoke` command and CI guard were added so stale-log-only deploy verification cannot silently return.

## Done

- Added `remote_epoch`, `fresh_smoke_default_epoch`, and `verify_fresh_backend_logs` to `deploy`.
- Updated `restart_all` to capture the remote restart boundary and run `verify_fresh_backend_logs "$smoke_since"` after `start.sh`.
- Added manual `./deploy fresh-smoke [epoch]`; without an epoch it checks remote logs updated in the last 15 minutes.
- Fresh smoke checks critical logs under `/opt/novaic/data/logs`: HTTP services, queue-service, task/saga worker representatives, outbox workers, health, scheduler, and subscriber.
- Added `scripts/ci/lint_deploy_fresh_smoke.py` to lock the deploy hook, command, critical logs, docs, and workflow wiring.
- Wired the lint into `.github/workflows/lint.yml`.
- Documented timestamp-aware fresh smoke in `docs/runbooks/deploy.md`.

## Verification

- `bash -n deploy`
- `bash -n scripts/start.sh`
- `python3 scripts/ci/lint_deploy_fresh_smoke.py`
- `python3 scripts/ci/check_start_config_contract.py`
- `python3 scripts/ci/lint_docs_status_consistency.py`
- `./scripts/ci/lint_current_docs_residue.sh`
- `python3 scripts/ci/lint_roadmap_ticket_archaeology.py`
- `git diff --check -- deploy docs/runbooks/deploy.md scripts/ci/lint_deploy_fresh_smoke.py .github/workflows/lint.yml`
- `python3 -m py_compile scripts/ci/lint_deploy_fresh_smoke.py`
- `./deploy __help_smoke__ | sed -n '1,80p'`

## Known Gaps

- This is a deploy-script and CI guard change; no remote production deploy was run in this ticket.
- Fresh log mtime proves logs were updated after the restart boundary. Full worker liveness supervision is handled by the separate runtime supervision gap.

## Artifacts

- `deploy`
- `scripts/ci/lint_deploy_fresh_smoke.py`
- `.github/workflows/lint.yml`
- `docs/runbooks/deploy.md`
