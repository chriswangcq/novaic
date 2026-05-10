# Cut Archive Finalize Stack Snapshots To SQLite Projection

## Problem Definition

`scope_end` root and child archive paths still call `_collect_active_stack(...)` before writing `wake_archived` and active-stack-finalized projection events. That makes archive/finalize event data depend on filesystem stack walking rather than the SQLite active-stack projection that now owns runtime stack state.

## Proposed Solution

Replace the archive/finalize stack snapshot source in `scope_end`:

- Read the active-stack projection at the beginning of the root archive path with `read_active_stack_projection(ws.operational_store, root_scope_id=req.scope_id, root_scope_path=active_path)`.
- Use `active_stack["frames"]` for `remaining_stack` calculation and `_finalize_active_stack_for_archive(...)`.
- Read the active-stack projection at the beginning of the child archive path after resolving `root_scope_id/root_scope_path`.
- Preserve existing idempotent already-archived paths, since they should not need a new stack read.
- Add or update lifecycle tests so root archive and wake/child archive finalize events use projection-derived frames and no file-walk stack collection is needed.

## Acceptance Criteria

- The `scope_end` root archive branch has no `_collect_active_stack(...)` call.
- The `scope_end` child archive branch has no `_collect_active_stack(...)` call.
- Wake archived/finalize event `remaining_stack` behavior remains correct for root archive and child/wake archive.
- Existing archive idempotency behavior is preserved.

## Verification Plan

- Run targeted archive/finalize lifecycle tests.
- Run a static section check over `scope_end` to confirm `_collect_active_stack` is absent and `read_active_stack_projection` is present.
- Run the full Cortex test suite if targeted tests pass.

## Risks

- Synthetic tests that archive scopes without creating active-stack projection rows may fail; those tests should be updated to use public lifecycle APIs or explicitly seed projection state.
- Root archive behavior needs care because an empty stack is valid and should finalize cleanly.

## Assumptions

- Phase 3B/3C projection writes are available before archive/finalize paths run.
- No backward-compatible file-walk fallback is required.
