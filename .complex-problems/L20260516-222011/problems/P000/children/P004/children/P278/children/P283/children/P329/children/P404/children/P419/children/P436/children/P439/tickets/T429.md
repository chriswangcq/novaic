# Ticket: Decide and clean materialized context endpoint ownership

## Problem Definition

`/v1/context/read`, `/v1/context/append`, `/v1/context/batch`, and `CortexBridge.read_context/append_context/append_context_batch` remain live. P438 proved they are not the authoritative LLM prepare source, but their current names and broad bridge methods can still mislead future code into using materialized projections as LLM history. They need explicit ownership, narrowing, migration, or deletion.

## Proposed Solution

- Audit every live runtime/Cortex usage of materialized context endpoints.
- Separate legitimate current owners from stale compatibility:
  - notification hint append/read idempotency,
  - assistant/system context projection writes,
  - tests for materialized projection API,
  - debug/read-only projection APIs,
  - dead compatibility.
- Rename or narrow bridge helpers where necessary so LLM prepare code cannot accidentally call projection helpers.
- Delete dead helpers/tests/docs if they are only compatibility residue.
- Run focused context/read/append and prepare-path tests.

## Acceptance Criteria

- Every materialized context endpoint/helper has an explicit current owner or is deleted.
- Runtime bridge names do not imply authoritative LLM history if they only manage notification/materialized projection state.
- No live LLM prepare code depends on materialized context projection.
- Focused runtime/Cortex tests pass.
- Any broader migration is split rather than half-implemented.

## Verification Plan

- Use P437 inventories as the starting evidence.
- Inspect and modify runtime context handlers / bridge helpers / tests as needed.
- Run focused runtime context-read/context-append tests and Cortex context event API tests.
- Run P438 prepare-path guard tests again after cleanup.

## Risks

- `context.read` currently appends notification hints idempotently. Blind deletion could break user-message notification delivery.

## Assumptions

- The endpoint can remain only if its name/ownership is explicit and it is not treated as LLM prepare history.
