# Runtime Local Shell Fallback Residue Audit result

## Summary

Audited Cortex/runtime/sandbox shell execution boundaries for hidden local fallback paths. The direct local shell/materialization path was already removed; the audit found one active adjacent residue: implicit `http://localhost:19996` shell API URL defaults. Spawned and completed P651/P652 to remove that residue from production and test helper paths.

## Findings and Fixes

- Confirmed `Workspace.materialize()` is deleted and no active local shell execution fallback remains in `Sandbox`.
- Confirmed remaining `novaic-cortex-sandbox-*` references are defensive rejection/test/tool-description paths, not live execution adapters.
- Removed implicit Cortex API URL defaults from `MountNamespaceLogicalFS`, `Sandbox`, `Cortex`, API construction, startup wiring, and docs.
- Removed test-helper URL default so test code also has explicit dependency boundaries.

## Verification

Evidence files:

- `.complex-problems/L20260516-222011/tmp/P648-runtime-fallback-postscan.txt`: found implicit `http://localhost:19996` default residue, which triggered P651.
- `.complex-problems/L20260516-222011/tmp/P651-focused-tests-rerun.txt`: focused shell/sandbox/API tests passed (`20 passed`).
- `.complex-problems/L20260516-222011/tmp/P652-helper-tests.txt`: helper-user tests passed (`86 passed`).
- `.complex-problems/L20260516-222011/tmp/P652-helper-postscan.txt`: no active `http://localhost:19996`, no hidden `cortex_api_url: str =`, and no active `/tmp/.novaic_env` fallback.

## Residual Risk

Low. Remaining legacy-string hit is only a negative assertion checking that `/tmp/.novaic_env.json` is absent from CLI source. Remaining explicit fake URLs are test literals, not hidden defaults.
