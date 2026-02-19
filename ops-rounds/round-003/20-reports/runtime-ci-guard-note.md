# Runtime CI Guard Note (Round 003)

## Purpose
Prevent regression where localhost health checks are routed through proxy env and return false failures.

## Guard Rule
- For localhost service readiness checks in contract/startup tests, use HTTP calls with `trust_env=False`.
- Do not rely on `NO_PROXY` alone for correctness in CI or heterogeneous dev environments.

## Applied Location
- `novaic-backend/tests/contract/test_runtime_orchestrator_process_startup.py`
  - helper: `_local_get(url, timeout)`
  - implementation: `httpx.Client(trust_env=False, timeout=timeout).get(url)`

## Why This Matters
- Without this guard, `httpx` can consume proxy env and return proxy-side `503` for `127.0.0.1`.
- This produces false negatives on startup health tests even when Runtime Orchestrator is healthy.

## Verification Command
- `pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- Expected: all tests pass.
