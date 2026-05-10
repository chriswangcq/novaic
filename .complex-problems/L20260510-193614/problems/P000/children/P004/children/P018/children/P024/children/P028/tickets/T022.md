# Wire Scope Archive Through Active Stack Finalize

## Problem Definition

`scope_end` still archives root/wake scopes with hard-coded empty `remaining_stack` in the semantic context event and without recording an operational finalize event. That leaves live archive behavior disconnected from the Phase 3B3A finalize helper.

## Proposed Solution

Wire scope archive through the active-stack finalize helper:

- Import and call `finalize_active_stack_projection` from the archive path.
- Capture the current active-stack snapshot before archive side effects.
- Pass the same remaining stack snapshot to `WakeArchived` context events when the archived scope is a wake.
- Use deterministic generation from the Workspace clock and explicit idempotency key derived from root scope id, archived scope id, and archive reason.
- Clear active-stack projection through the helper after the event is recorded.
- Keep existing `scope_end` response shape and idempotent archive behavior.

## Acceptance Criteria

- Live root/wake archive path records `active_stack_finalized` operational event.
- The operational event payload contains actual `remaining_stack`, `top_scope_id`, and `reason`.
- Projection is empty after archive/finalize.
- Context `WakeArchived` event receives the actual remaining stack snapshot where wake archive is involved.
- Existing archive responses remain compatible.

## Verification Plan

- Add or update context/scope lifecycle tests for scope_end with empty stack and non-empty child stack.
- Check operational store events after archive.
- Run affected archive/context tests.
- Run full `novaic-cortex/tests`.

## Risks

- Archive idempotency may require event idempotency to be stable across active and already-archived paths.
- Existing context projection may expect `remaining_stack` as a list of scope IDs; if operational stack frames are richer, context event payload must remain semantically compatible or tests must be updated deliberately.
- File-walk stack snapshot is still temporary read authority until P019/P020.

## Assumptions

- Scope archive should finalize the root active-stack projection for the active session root.
- Rich operational frames can be reduced to scope-id lists for semantic context events if needed.
