# Runtime Probe Guard Policy (Round 007)

## Policy Goal
Prevent proxy-related false negatives for localhost startup/health contract checks.

## Scope
- Target path: `novaic-backend/tests/contract/test_*.py`
- Enforced subset: files that contain localhost markers (`127.0.0.1`, `localhost`, `/api/health`)

## Mandatory Pattern
- Import shared helper: `from .http_probe import local_get`
- Use `local_get(...)` for localhost probes
- Shared helper must keep `trust_env=False`

## Forbidden Pattern (In Scoped Files)
- `httpx.get/post/put/delete/patch(...)`
- `httpx.Client(...)`

## Enforcer
- Script: `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
- CI integration: `.github/workflows/ci.yml` step `Localhost probe safety guard (Round 006)` in Python job
