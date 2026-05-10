# Result: Cortex LogicalFS Adapter Migrated

## Summary

Migrated `novaic_cortex.logical_fs` from an in-module generic filesystem implementation to a Cortex adapter over `novaic-logicalfs`.

## Done

- Replaced duplicated Cortex-local materialization/diff/sanitize/cwd helpers with calls to `LocalLogicalFSProvider`.
- Kept Cortex ownership of Workspace snapshot creation, generated `.novaic_env.json`, subagent RW layout env, shell capability CLI injection, and applying RW patches back to Workspace.
- Added `LogicalFSLayout.writable_dirs` so generic LogicalFS can create explicit writable directories without turning every directory into an env variable.
- Removed `_logical_rw_changes` from the Cortex public import path and moved deletion/diff coverage to the generic LogicalFS tests.
- Added Cortex sandbox wiring assertions that the process runner sees mounted capability scripts (`agentctl`, `cortex`, `devicectl`) and stable `/cortex` env.

## Verification

- `PYTHONPATH=novaic-logicalfs pytest -q novaic-logicalfs/tests` passed: 4 tests.
- `PYTHONPATH=novaic-logicalfs:novaic-sandbox-sdk:novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` passed: 3 tests.
- `PYTHONPATH=novaic-logicalfs:novaic-sandbox-sdk:novaic-common:novaic-cortex pytest -q novaic-cortex/tests` passed: 344 passed, 40 skipped.
- Cortex scan for displaced generic helper names found no active helper definitions under `novaic-cortex/novaic_cortex`; the names only remain in the generic `novaic-logicalfs` substrate and one old real-shell test function name.
- LogicalFS package forbidden import scan found no product/service imports in code modules; README/tests only mention subagents as example path strings.

## Residual Risk

- P003/P004 still need final script/deploy wiring and broader residue cleanup checks.
- Existing real-shell tests remain skipped unless `NOVAIC_CORTEX_REAL_SANDBOXD_TESTS=1`; full live shell verification belongs to the later deploy/smoke phase.
