# Check: P002 Cortex Adapter Migration

## Verdict

Success.

## Evidence

- `novaic_cortex.logical_fs` now imports `LocalLogicalFSProvider`, `LogicalFSSnapshot`, `LogicalFSLayout`, `LogicalFSEnv`, and `LogicalFSPatch` from `logicalfs`.
- Cortex-local adapter code now owns only Workspace snapshot/patch translation, generated env file, subagent RW layout, shell capability scripts, and sandbox bind plan.
- Old Cortex duplicate helper exports were removed (`_logical_rw_changes` is no longer exported or imported from `novaic_cortex.sandbox`).
- Focused and broad tests passed:
  - `novaic-logicalfs/tests`: 4 passed.
  - Cortex sandbox wiring/no-local-fallback tests: 3 passed.
  - Full Cortex non-real-shell suite: 344 passed, 40 skipped.
- Residue scan found no generic helper definitions under `novaic-cortex/novaic_cortex`.

## Criteria Map

- Delegate generic LogicalFS mechanics to `novaic-logicalfs`: satisfied.
- Preserve stable `/cortex/ro`, `/cortex/rw`, `/cortex/bin` env and mount contract: satisfied by adapter code and sandbox wiring test.
- Preserve capability CLI injection: satisfied by sandbox wiring test asserting `agentctl`, `cortex`, and `devicectl` exist in the mounted bin directory.
- Avoid product/service dependencies inside `novaic-logicalfs`: satisfied by import scan.
- Remove old generic duplicate implementation from Cortex: satisfied for active code.

## Execution Map

- `LocalLogicalFSProvider.materialize()` now handles file view creation and cwd/env baseline.
- `LocalLogicalFSProvider.observe_patch()` now detects RW upserts/deletes.
- `MountNamespaceLogicalFS` converts Cortex Workspace trees to `LogicalFSSnapshot`, translates `LogicalFSPatch` back to `/rw/...`, and injects Cortex-specific runtime details.

## Stress Test

The generic LogicalFS tests cover snapshot materialization, explicit env layout, writable directory creation, cwd escape rejection, output sanitization, and upsert/delete patch observation. Cortex tests cover sandboxd mount contract and absence of local fallback.

## Residual Risk

P003/P004 still own final execution-path validation, deploy/script wiring, and full residue cleanup. This does not block P002 because the adapter migration itself is complete and tested.
