# Check: Active Path Audit Complete

## Summary

The audit solves P001: it identifies the current active shell path, old temp-projection logic, tests that encode old behavior, and host substrate constraints for true `/cortex` mount semantics.

## Criteria Map

- Active entry points listed: satisfied by R000.
- Old temp-projection/gating logic listed: satisfied by R000.
- Host mount/FUSE/proot/unshare support checked: satisfied by R000.
- Implementation constraints recorded: satisfied by R000 known gap.

## Execution Map

- Result IDs checked: R000.
- Evidence came from `rg`, code slices, and Python host capability checks.

## Stress Test

The audit explicitly handles the hard case where the desired final architecture depends on host mount capabilities that are absent. It does not silently claim true `/cortex` hidden-literal semantics are available.

## Residual Risk

- The worktree is dirty, so later implementation must avoid reverting unrelated changes.
- Host capability could differ in deployment; tests should therefore encode provider capabilities rather than hard-code local host assumptions as product truth.
