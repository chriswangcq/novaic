# Cortex handler and bridge classification ticket

## Problem Definition

Cortex handler and bridge code contains scope-end/archive, round, and counter hits. These must be classified so session_generation remains explicit while Cortex counters remain harmless.

## Proposed Solution

Inspect `task_queue/handlers/cortex_handlers.py` and `task_queue/utils/cortex_bridge.py`, classify all generation-like and counter hits, patch any session identity fallback, and run focused tests.

## Acceptance Criteria

- Scope-end/archive `session_generation` is explicit and positive/non-negative as designed.
- `round_num` and Cortex counter defaults are classified as non-session authority.
- No Cortex handler/bridge path infers session generation from current active state.
- Focused tests pass.

## Verification Plan

- Run targeted guard over Cortex handler/bridge files.
- Inspect source around hits.
- Run focused Cortex handler/bridge/session archive tests from runtime and Cortex where practical.

## Risks

- Cortex round counters are operational metadata; do not confuse them with session authority.

## Assumptions

- Cortex archive identity has already been tightened in previous children; this ticket verifies handler/bridge residue only.
