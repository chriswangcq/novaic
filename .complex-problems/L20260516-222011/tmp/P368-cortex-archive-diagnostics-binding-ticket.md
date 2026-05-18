# Ticket: Cortex Archive Diagnostics Binding

## Problem Definition

The queue wake-finalize flow now carries explicit finalize identity, but the Cortex archive boundary still risks recording generic archive diagnostics from Cortex active-stack state. `ScopeEndRequest` and `CortexBridge.scope_end` need to preserve explicit finalize payload identity so archived context events cannot silently bind to the wrong wake.

## Proposed Solution

Audit and update the task-queue-to-Cortex scope-end path. Carry explicit finalize diagnostics from wake-finalize payloads through `task_queue/handlers/cortex_handlers.py`, `task_queue/utils/cortex_bridge.py`, and `novaic-cortex/novaic_cortex/api.py` into Cortex archive/context-event records. Require positive `session_generation` where archive diagnostics are supplied, avoid active-generation inference for finalize identity, and add focused tests for valid and missing/stale generation behavior.

## Acceptance Criteria

- `CORTEX_SCOPE_END` handler forwards explicit `session_generation`, `finalize_reason`, and remaining-stack diagnostics to Cortex instead of dropping them.
- Cortex API request/schema accepts explicit archive diagnostics without falling back to inferred active generation for those fields.
- Valid archive records the intended finalize reason/generation/remaining-stack metadata in the archive/context event.
- Missing or non-positive generation cannot archive through the finalize diagnostics path.
- Tests cover the task handler/bridge boundary and the Cortex archive recorder.
- Residue search finds no direct archive path writing finalize diagnostics from inferred active lookup.

## Verification Plan

- Run focused unit tests for task queue Cortex handlers/bridge.
- Run focused Cortex scope archive tests.
- Run `python3 -m py_compile` for changed task-queue and Cortex modules.
- Run residue search for `scope_end`, `finalize_reason`, `session_generation`, `remaining_stack`, and archive event writers across `novaic-agent-runtime/task_queue`, `novaic-cortex/novaic_cortex`.

## Risks

- The archive API may have downstream callers that do not yet provide diagnostics; keep non-finalize callers valid while making finalize diagnostics explicit where present.
- Context event schema may already be consumed by tests or UI; changes should be additive and stable.

## Assumptions

- P366 source map is accurate: the gap is boundary propagation and archive metadata binding, not queue session finalize decision logic.
- Existing old data compatibility is not required; tests may be updated to the new explicit contract.
