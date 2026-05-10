# Sandboxd extraction verification completed

## Summary

Verified the sandboxd extraction across common contracts, service behavior, Cortex wiring, deployment scripts, live local HTTP service smoke, and residue scans. Remote production deployment was not executed in this ticket.

## Done

- Ran focused and broader common sandbox tests.
- Ran sandboxd service tests.
- Ran Cortex sandboxd wiring and sandbox-focused tests.
- Ran shell/deploy syntax checks and deploy fresh-smoke lint.
- Started `sandboxd` locally on `127.0.0.1:19994`, checked `/health`, called `/v1/execute`, then stopped it.
- Re-ran residue scans for old Cortex command wrapping.

## Evidence

- `PYTHONPATH=novaic-common pytest -q novaic-common/tests/test_sandbox_infra.py` -> `9 passed in 1.06s`.
- `PYTHONPATH=novaic-common:novaic-sandbox-service pytest -q novaic-sandbox-service/tests` -> `5 passed in 1.27s`.
- `PYTHONPATH=novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` -> `3 passed in 0.18s`.
- `bash -n scripts/start.sh && bash -n deploy && python3 scripts/ci/lint_deploy_fresh_smoke.py` -> passed with `lint_deploy_fresh_smoke OK`.
- Local live smoke:
  - `/health` -> `{"status":"ok","service":"sandboxd","contract_version":"sandboxd/v1"}`.
  - `/v1/execute` with `printf live-sandboxd` -> `exit_code=0`, stdout base64 decodes to `live-sandboxd`.
- Broader tests:
  - `PYTHONPATH=novaic-common pytest -q novaic-common/tests` -> `148 passed in 2.57s`.
  - Cortex sandbox-focused set -> `3 passed, 21 skipped in 0.18s`.

## Residual Risk

- Remote deployment/fresh-smoke was not executed here. Local macOS cannot prove the Linux mount namespace execution path live through Cortex; the contract is covered by fake-runner integration tests, and real Linux proof should come from deployment smoke.
