# Subagent finalize status identity aggregate verification

## Problem Definition

P357, P358, and P359 changed the terminal subagent status path across payload builders, handlers, and wake-finalize ordering. P360 must verify the whole path as one contract and look for residual compatibility or bypass routes.

## Proposed Solution

1. Run focused tests that cover:
   - wake-finalize payload builders.
   - subagent terminal status handlers.
   - wake-finalize step order and generated task dependencies.
   - session-ended finalize rejection behavior.
   - saga DAG explicit dependency support.
2. Run source guards over touched runtime files for:
   - `last_scope_id` in live source.
   - generation defaulting such as `or 0`.
   - terminal status `entity_update()` calls before identity validation.
3. Inspect topic/handler usage to confirm terminal Business status mutations only flow through `handle_subagent_set_sleeping()` / `handle_subagent_set_completed()` and those handlers enforce identity.
4. Record residual risk explicitly, especially P351 recovery/compensation identity work outside this child.

## Acceptance Criteria

- Focused test suite passes.
- Source guards show no live `last_scope_id` or session generation defaulting residue in the touched runtime files.
- Terminal subagent status update paths are covered by the new identity checks and session-ended gate.
- Recovery/compensation scope is acknowledged rather than hidden.

## Verification Plan

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_runtime_tool_path_contract.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/integration/test_saga_dag_refactor.py`
- `rg` guards over `task_queue/sagas/wake_finalize.py`, `task_queue/handlers/subagent_handlers.py`, `task_queue/handlers/session_handlers.py`, `task_queue/saga.py`, and related tests.
- Manual source inspection of terminal status mutation handlers and wake-finalize DAG specs.

## Risks

- Aggregate verification may find a residual path that should become a follow-up rather than being waved through.
- Existing unrelated dirty worktree changes should not be reverted or conflated with P360 evidence.

## Assumptions

- P357, P358, and P359 have all passed their own success checks.
