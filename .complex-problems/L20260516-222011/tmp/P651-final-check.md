# P651 final strict success check

## Status

success

## Result IDs

- R641
- R642

## Evidence

- R641 removed production/runtime `http://localhost:19996` defaults from LogicalFS/Sandbox/Cortex/API/startup wiring and passed the focused shell/sandbox tests (`20 passed`).
- R642 removed the remaining test-helper fake URL default and passed all helper-user tests (`86 passed`).
- `.complex-problems/L20260516-222011/tmp/P652-helper-postscan.txt` shows no `cortex_api_url: str =` hidden default and no `http://localhost:19996` fallback in Cortex runtime/helper/test/doc/start files.
- The only `/tmp/.novaic_env` hit is a negative test assertion verifying the old fallback is absent from source.

## Criteria Map

- Removes `http://localhost:19996` defaults in `Sandbox` and `MountNamespaceLogicalFS`: satisfied.
- Passes Cortex API URL explicitly from runtime/API construction path and test helpers: satisfied after R642.
- Keeps shell capability commands fail-closed when `NOVAIC_API` is missing: satisfied by focused shell capability tests in R641.
- Adds/updates regression tests proving no `/tmp/.novaic_env.json` or localhost fallback exists in CLI/shell capability paths: satisfied by `test_pr75_proxy_boundary.py`, shell capability tests, and fallback scans.

## Execution Map

- P651 implementation removed production fallback and exposed missing helper residue.
- P652 follow-up closed that helper residue.
- Verification covered production constructor paths, API endpoint wiring, shell capabilities, and all helper-using tests.

## Stress Test

The first check intentionally failed P651 on a test-helper default rather than accepting a near miss. The follow-up then removed that residue and reran broad helper tests plus source scans. This is consistent with one-go skepticism.

## Residual Risk

Low. There may still be repeated explicit `http://cortex.test` literals in tests, but repetition is intentionally explicit and no longer hides constructor dependencies.
