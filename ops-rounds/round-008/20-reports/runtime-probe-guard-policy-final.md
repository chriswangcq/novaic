# Runtime Probe Guard Policy (Final - Round 008)

## Scope Policy
- Guard root: `novaic-backend/tests/contract/`
- Allowlist patterns:
  - `test_*startup*.py`
  - `test_*health*.py`
- Only allowlisted files are enforced by probe-safety guard.

## Enforcement Rules
- Must import shared helper: `from .http_probe import local_get`
- Must call `local_get(...)` for localhost probe requests
- Shared helper file (`tests/contract/http_probe.py`) must keep `trust_env=False`
- Forbidden in allowlisted files:
  - `httpx.get/post/put/delete/patch(...)`
  - `httpx.Client(...)`

## Enforcement Entry Points
- Guard script:
  - `novaic-backend/scripts/tools/ci_guard_localhost_probe_safety.sh`
- CI integration:
  - `.github/workflows/ci.yml` -> Python job -> step `Localhost probe safety guard (Round 006)`

## Ownership and Cadence
- policy owner: Runtime Team
- co-owner: Platform Team
- review cadence: weekly (every Friday) and mandatory review on new startup/health contract test additions
