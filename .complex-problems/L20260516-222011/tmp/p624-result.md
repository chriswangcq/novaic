# Runtime Sandbox SDK Call Site Residue Result

## Summary

Closed P624 split children. Runtime active shell execution does not bypass sandboxd: shell handlers call Cortex `/v1/internal/shell` through `CortexBridge`, while runtime subprocess usage is limited to service/process supervision and tests.

## Done

- P626 verified active shell handler wiring: `_exec_shell -> CortexBridge.shell_exec -> /v1/internal/shell`.
- P627 classified runtime legacy/direct-execution residue and found no active user shell bypass.
- Focused runtime shell/tool path/roster/residue tests passed after correct cwd invocation.

## Verification

- P626 check C655 succeeded, citing result R614.
- P627 check C656 succeeded, citing result R615.
- P626 tests: 7 passed.
- P627 tests: 17 passed plus 9 tool path contract tests.

## Known Gaps

- Generated untracked `__pycache__` files should be cleaned during final workspace hygiene.
- Runtime delegates to Cortex rather than importing `sandbox_sdk` directly; this is intended because Cortex owns the shell/sandboxd service boundary.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-classification.md`
- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-classification.md`
- `.complex-problems/L20260516-222011/tmp/p626-runtime-sdk-wiring-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-tests-rerun.txt`
- `.complex-problems/L20260516-222011/tmp/p627-tool-path-contract-tests.txt`
