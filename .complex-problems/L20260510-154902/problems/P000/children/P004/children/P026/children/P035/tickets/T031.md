# Extract reusable tool step normalization

## Problem Definition

Tool step event emission needs final payload refs before legacy file projection. `Workspace.write_step` currently owns validation and payload normalization internally, which makes event-first writing hard.

## Proposed Solution

- Extract a `normalize_tool_step` helper/method in `Workspace`.
- The helper validates tool step shape and externalizes inline payloads, returning a normalized copy.
- `write_step` uses the normalized copy instead of mutating caller input in place.
- Add focused tests that prove payload ref normalization and non-mutation.

## Acceptance Criteria

- Normalization returns final `payload_ref`.
- Caller input is not mutated unexpectedly.
- `write_step` behavior remains compatible.
- Focused workspace tests pass.

## Verification Plan

- Add/update workspace tests.
- Run step/workspace tests.
- Run full Cortex suite.

## Risks

- Existing tests may rely on mutation accidentally; if so, treat mutation as residue and update tests.

## Assumptions

- Event emission itself is P036.
