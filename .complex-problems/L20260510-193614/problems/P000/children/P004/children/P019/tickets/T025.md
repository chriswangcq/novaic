# Cut Runtime Stack Reads To SQLite Active Stack

## Problem Definition

Runtime stack reads and LIFO checks still use file-walk authority (`_collect_active_stack`, `resolve_active_scope_path`) even though Phase 3B now writes SQLite active-stack projection. Phase 3C must switch control-plane reads to operational SQLite while preserving API response semantics and structured error behavior.

## Proposed Solution

Perform the cutover in explicit subproblems:

- Add a small read adapter that loads active-stack frames from operational SQLite and resolves the current active scope path from frame data.
- Switch `context_status` default stack frames to SQLite projection.
- Switch `skill_begin` parent/top selection to SQLite projection rather than file-walk active path.
- Switch `skill_end` LIFO validation and stack-empty/mismatch responses to SQLite projection.
- Add fresh registry/workspace instance tests proving SQLite projection survives process-local workspace reconstruction.
- Keep `_collect_active_stack` only as temporary trace/debug/fallback surface until P020 quarantines file-walk authority.

## Acceptance Criteria

- `context_status` default stack comes from SQLite active-stack projection.
- `skill_begin` chooses parent path/top from SQLite projection.
- `skill_end` validates current top from SQLite projection.
- Wrong-scope and stack-empty errors keep current response shape.
- Fresh workspace/registry test proves open-child behavior uses persisted SQLite state.
- Full Cortex tests pass.

## Verification Plan

- Add focused tests for status, begin parent selection, end mismatch/empty, and fresh workspace read.
- Run targeted lifecycle/status tests.
- Run static search to confirm live control reads no longer call `_collect_active_stack` for these paths.
- Run full `novaic-cortex/tests`.

## Risks

- Active stack frames must include enough `scope_path` and `parent_path` data; Phase 3B added this but cutover must fail loudly if old rows are incomplete.
- Some endpoints still need file-walk routing until P020; avoid broad deletion here.
- Scope archive/finalize can clear projection, so read code must handle empty projection cleanly.

## Assumptions

- Existing persisted test/workspace data can be discarded; no backwards compatibility for old rows without path fields is required.
- P020 owns quarantine/deletion of remaining file-walk authority after this cutover.
