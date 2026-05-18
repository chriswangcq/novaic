# Fix remaining live generation coercions

## Problem Definition

Three live generation boundaries still coerce input with raw `int(...)` instead of rejecting invalid generation values explicitly: two Cortex operational store writes and one runtime session attach active-state read.

## Proposed Solution

Patch the runtime attach path to use the existing positive generation validator, patch Cortex operational store write paths to use the existing non-negative generation validator, and add focused tests proving bool and negative values are rejected at the patched store/projection boundaries. Then rerun focused tests and cross-repo guards until the target residue pattern has no unclassified live matches.

## Acceptance Criteria

- `novaic-agent-runtime/queue_service/session_repo.py` no longer uses raw `int(...)` for the attach path active session generation.
- `novaic-cortex/novaic_cortex/operational_store.py` no longer uses raw `int(generation)` in live write paths.
- Focused runtime and Cortex tests cover the patched behavior.
- Cross-repo generation guard returns no raw live generation coercion matches in the target runtime/Cortex directories.
- Any remaining active/finalize/archive guard hits are classified with file evidence.

## Verification Plan

Run Python compile checks for changed modules, focused runtime tests covering attach/finalize/session state boundaries, focused Cortex tests covering operational store and active stack projection boundaries, and the cross-repo `rg` guard commands used by P380.

## Risks

- Cortex operational store may permit generation `0` for valid initial events, so the helper must be non-negative rather than positive.
- Runtime active session generation is semantically positive; using a non-negative helper there would keep the old silent-default failure mode alive.

## Assumptions

- No backward compatibility with malformed bool/missing/negative generation values is required.
- Existing tests that build valid generation `0` Cortex records should continue to pass.
