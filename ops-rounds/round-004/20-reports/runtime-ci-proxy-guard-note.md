# Runtime CI Proxy Guard Note (Round 004)

## Guard Objective
Keep localhost readiness checks deterministic across CI/dev environments that may inject proxy settings.

## Enforced Pattern
- For localhost startup probes, use HTTP client calls with `trust_env=False`.
- Centralize probe helper to avoid accidental direct `httpx.get(...)` usage with env proxy inheritance.

## Applied Reference
- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
  - helper: `_local_get(url, timeout)`
  - implementation: `httpx.Client(trust_env=False, timeout=timeout).get(url)`

## Regression Signature (Historical)
- Symptom: startup contract health probe sees proxy `503` while runtime process is actually healthy.
- Existing reproduction notes:
  - `ops-rounds/round-002/20-reports/runtime-startup-troubleshooting.md`

## Verification Command
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- Expected result: all tests pass.
