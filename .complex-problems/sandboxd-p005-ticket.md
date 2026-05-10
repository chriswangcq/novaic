# Clean stale in-process sandbox residue

## Problem Definition

After moving the active server path to sandboxd, leftover Cortex command-wrapping helpers and ambiguous in-process runner defaults can mislead future work. The code should make the active path and test adapter boundary obvious.

## Proposed Solution

Remove unused LogicalFS command wrapping methods, remove direct `build_bind_mount_command` imports from Cortex LogicalFS, add comments naming the direct runner as a library/test adapter, and run residue scans over active source.

## Acceptance Criteria

- `logical_fs.py` no longer exposes unused `process_command` or `_mount_namespace_command`.
- `sandbox.py` active path only requests `process_mount_plan`.
- Any direct runner default is documented as a library/test adapter; production server startup remains sandboxd-only.
- Source scans find no old command-wrapping path in Cortex orchestration.

## Verification Plan

- Run focused Cortex wiring tests.
- Run source scans for `process_command`, `_mount_namespace_command`, and `build_bind_mount_command` in Cortex active modules.

## Risks

- Some tests may still instantiate `Sandbox` directly; those remain explicit library-level tests, not production wiring.

## Assumptions

- Full deletion of `AsyncProcessRunner` is not correct because sandboxd itself uses it as the generic process substrate.
