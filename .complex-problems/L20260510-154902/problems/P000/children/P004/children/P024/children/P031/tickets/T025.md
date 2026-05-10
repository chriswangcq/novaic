# Verify root/wake/notification cutover

## Problem Definition

After P029 and P030, audit that root/wake lifecycle and notification attachment are now event-emitting paths, and that any remaining legacy writes are either transitional artifacts or explicitly owned by later Phase 3 children.

## Proposed Solution

- Run focused lifecycle/notification tests.
- Run full Cortex suite.
- Static scan the relevant API/workspace paths for lifecycle/notification writes.
- Confirm remaining legacy writes are not hidden bypasses for P024-owned facts.
- Record open work for later Phase 3 children.

## Acceptance Criteria

- Focused tests pass.
- Full Cortex suite passes.
- Static scan confirms root/wake/notification paths call `ContextEventWriter`.
- Any remaining legacy writes for these facts are documented as transitional/debug or owned by P028 cleanup.

## Verification Plan

- Run `pytest` focused and full.
- Run `rg` scans for `scope_create`, `scope_end`, `scope_append_input`, `append_input_message_ids`, and event writer usage.

## Risks

- Static scan could miss indirect paths; if unclear, create a follow-up rather than marking success.

## Assumptions

- Context append, tool step, and skill lifecycle cutovers remain separate P025-P027 children under P004.
