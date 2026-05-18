# Runtime continuity and context.read residue classification check

## Summary

`P162` is solved. Remaining runtime continuity/context-read paths are classified: context-read is active-safe inspection/notification hinting; wake/session continuity is active-safe current-input registration plus generation-checked attach; production `read_context` callers are inventoried and no unclassified provider-authority path remains.

## Evidence

- `C169`: context-read handler classification.
- `C170`: runtime wake/session continuity classification and cwd-dependent test repair.
- `C171`: full runtime `read_context` caller inventory.
- `R158`: consolidated child outcomes.

## Criteria Map

- `context_handlers.py`, `runtime_handlers.py`, and bridge/context-read callers mapped: satisfied by child checks.
- Remaining residue classified as active-safe/dead/stale: satisfied; no active stale provider-input path found.
- Active stale provider-input path fixed/split: none found; one test hidden input fixed.
- Focused tests/static guards identified/run: satisfied by `31`, `35`, and `41` passed test slices.

## Execution Map

- `T159` split into `P173`, `P174`, and `P175`.
- All children completed successfully before parent result.

## Stress Test

The guard set catches raw message replay, context-read body fetching, handler/provider context authority, stale attach generation, and retired continuity injection reintroduction.

## Residual Risk

- None for this residue classification scope. Overall parent `P135` still has `P163` open for final regression coverage audit.

## Result IDs

- R158
