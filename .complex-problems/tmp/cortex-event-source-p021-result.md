# Projection stale sibling suppression result

## Summary

Implemented stale open sibling suppression in the pure projector. When a newer open skill appears under the same parent, older still-open sibling frames and their descendants are removed from the active stack, and their buffered messages remain invisible to the projected LLM context.

## Done

- Added `_suppress_open_siblings` and `_is_stale_scope_or_descendant` to `context_event_projection.py`.
- Invoked suppression before pushing a new `SkillScopeOpened` frame.
- Added tests for:
  - newer sibling replacing older open sibling;
  - stale descendant removal;
  - ordinary nested child not being suppressed.

## Verification

- `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_projection.py tests/test_context_event_model.py tests/test_context_event_store.py -q` passed: 59 passed.
- Static scan found no Workspace/file/legacy DFS/payload/env/time/id dependency in `context_event_projection.py`.

## Known Gaps

- None for stale sibling suppression.
- Tool call/result placement remains open in P016.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`
