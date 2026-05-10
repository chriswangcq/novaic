# Deployment wiring includes sandboxd

## Summary

Registered sandboxd as a first-class backend service on port `19994`, wired local startup to start it before Cortex, and updated deploy/status/log smoke paths so production restarts include sandboxd.

## Done

- Added `services.sandboxd.url` to `novaic-common/config/services.json`.
- Added `ServiceConfig.SANDBOXD_URL/HOST/PORT`.
- Updated `scripts/start.sh` to stop, wait-free, start, wait, and log sandboxd.
- Updated Cortex startup in `start.sh` to pass `--sandboxd-url`.
- Updated `deploy services`, single-service deployment, fresh-log smoke, status, logs, help, and command dispatch to include sandboxd.
- Updated deploy fresh-smoke lint to require `sandboxd.log`.

## Evidence

- `bash -n scripts/start.sh && bash -n deploy` passed.
- `PYTHONPATH=novaic-common python - <<'PY' ... ServiceConfig.SANDBOXD_URL ... PY` printed `http://127.0.0.1:19994 19994`.
- `python3 scripts/ci/lint_deploy_fresh_smoke.py` -> `lint_deploy_fresh_smoke OK`.
- `rg -n "novaic-sandbox-service" deploy scripts/start.sh scripts/build-all.sh novaic-common/config/services.json` shows deploy/start wiring.

## Residual Risk

- Remote deployment has not been run in this ticket; this ticket prepares the deploy path. Actual deploy/smoke is covered later.
