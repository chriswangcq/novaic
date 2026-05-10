# Sandboxd process-boundary guardrail result

## Summary

Added sandbox-service boundary tests that keep sandboxd process-only. The tests
forbid sandbox-service source from importing Cortex, Blob Service, or LogicalFS
modules, and forbid obvious workspace ownership terms such as `Workspace`,
`CortexStore`, `BlobCortexStore`, `agent_id`, `scope_id`, `subagent`, `/ro/`,
and `/rw/`.

## Done

- Added `novaic-sandbox-service/tests/test_sandbox_boundary.py`.
- Verified sandbox-service source has no direct Cortex/Blob/LogicalFS imports.
- Verified sandbox-service source has no workspace/scope/subagent ownership
  vocabulary.
- Confirmed deployment/start scripts still run sandboxd as `novaic-sandbox-service`
  on port `19994` and Cortex is configured with `--sandboxd-url`.

## Verification

- Ran sandbox-service tests:
  - `PYTHONPATH=.:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q`
  - Result: `13 passed`.
- Ran focused residue scan:
  - `rg -n "novaic_cortex|blob_service|BlobCortexStore|CortexStore|Workspace|agent_id|user_id|scope_id|subagent|/ro/|/rw/|logicalfs|LogicalFS" novaic-sandbox-service/sandbox_service`
  - Result: no matches.
- Ran deployment reference scan:
  - `scripts/start.sh` launches `main_sandbox_service.py` on `19994`.
  - `deploy` syncs and installs `novaic-sandbox-service`, exposes `sandboxd`
    deploy/log commands, and includes `sandboxd.log`.
  - `novaic-cortex/novaic_cortex/main_cortex.py` receives `--sandboxd-url` and
    installs `SandboxdClient`.

## Known Gaps

- none for P003. The service is guarded as process-only.

## Artifacts

- `novaic-sandbox-service/tests/test_sandbox_boundary.py`
