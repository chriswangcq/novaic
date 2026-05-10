# Sandboxd service completed

## Summary

Created `novaic-sandbox-service` as a standalone FastAPI server with health and execute endpoints. The service uses only `novaic-common` sandbox contracts and process primitives, and owns process execution behind `/v1/execute`.

## Done

- Added `main_sandbox_service.py` entrypoint.
- Added `sandbox_service.main.create_app` with `/health`, `/api/health`, and `/v1/execute`.
- Added service validation for explicit timeout, cwd, mount source, mount point, and stable cwd.
- Added service requirements.
- Added tests for health, successful execution, timeout result, invalid mount source, and mount plan propagation to the runner.

## Evidence

- `PYTHONPATH=novaic-common:novaic-sandbox-service pytest -q novaic-sandbox-service/tests` -> `5 passed in 1.27s`.
- `rg -n "novaic_cortex|blob_service|agent_id|Workspace|Cortex|novaic-agent-runtime" novaic-sandbox-service/sandbox_service novaic-sandbox-service/tests || true` -> no matches.

## Residual Risk

- The Cortex active path is not wired to this service yet; that is tracked by P003.
