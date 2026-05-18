# P651 strict success check

## Status

not_success

## Result IDs

- R641

## Evidence

- Focused Cortex tests passed: `20 passed in 2.45s` in `.complex-problems/L20260516-222011/tmp/P651-focused-tests-rerun.txt`.
- Runtime fallback scan in `.complex-problems/L20260516-222011/tmp/P651-runtime-fallback-postscan.txt` showed no active `http://localhost:19996` production runtime fallback and no active `/tmp/.novaic_env.json` runtime dependency.
- The same scan still found `novaic-cortex/cortex_tests/workspace_test_utils.py:42: cortex_api_url: str = "http://cortex.test"`.

## Criteria Map

- Remove `http://localhost:19996` defaults in `Sandbox` and `MountNamespaceLogicalFS`: satisfied.
- Pass Cortex API URL explicitly from runtime/API construction path: satisfied.
- Keep shell commands fail-closed when `NOVAIC_API` is missing: satisfied by focused shell capability tests.
- Tests and helpers pass explicit URLs: partially satisfied; direct Sandbox tests pass explicit URLs, but the shared Cortex test helper still has a default fake URL.

## Execution Map

- Implemented explicit `cortex_api_url` plumbing across API, runtime, Sandbox, LogicalFS, startup script, and docs.
- Updated direct Sandbox tests and endpoint wiring test to provide explicit fake URL.
- Ran focused test suite and fallback scans.

## Stress Test

The targeted `rg` scan intentionally searched for fallback strings and constructor defaults. It found a remaining helper-level default. That is not production code, but it is exactly the kind of residue that can let future tests omit dependencies and miss wiring bugs.

## Residual Risk

Leaving the test helper default would normalize implicit test setup. Future tests could instantiate `Cortex` without proving the URL came from their fixture or service boundary. This is small but violates the explicit dependency principle, so P651 is not fully closed.
