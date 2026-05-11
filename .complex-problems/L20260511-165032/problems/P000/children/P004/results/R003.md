# Context Event Source Cutover Audit Result

## Summary

The active LLM context assembly path is connected to the ContextEvent read model and does not use the old DFS/materialized-context fallback. I found no live `prepare_for_llm` fallback to `context.jsonl`, `summary.md`, `StepTree`, or `ContextEngine`.

There is still misleading naming/comment residue around ContextEngine/DFS, and the materialized `context.jsonl` projection remains for inspection/debug and notification de-duplication. Those are not active LLM assembly sources.

## Done

- Inspected `novaic-cortex/novaic_cortex/api.py` around `/v1/context/prepare_for_llm` and `/v1/context/status`.
- Inspected `novaic-cortex/novaic_cortex/context_event_read_model.py`.
- Inspected materialized context helpers in `novaic-cortex/novaic_cortex/workspace.py`.
- Inspected runtime handlers that call Cortex prepare/status/read endpoints.
- Searched for old DFS/read fallback markers: `ContextEngine`, `StepTree`, `prepare_messages_for_llm`, `_collect_active_stack`, `resolve_active_scope_path`, `read_context`.
- Ran targeted context cutover tests.

## Verification

- `context_prepare_for_llm()` constructs `ContextEventReadModel(...).prepare()` and returns its messages/stack/token estimate.
- `ContextEventReadModel.prepare()` reads `ContextEventStore.read_events()`, raises `ContextEventReadModelResetRequired` when no event stream exists, projects with `project_context_events()`, then applies budget compaction.
- `context_status(include_usage=True)` also uses `ContextEventReadModel`; default `include_usage=False` uses SQLite active-stack projection for cheap operational stack checks, not DFS rendering.
- Guard tests pass:

```text
PYTHONPATH=... pytest -q \
  novaic-cortex/tests/test_context_event_no_compat.py \
  novaic-cortex/tests/test_context_event_read_source_guards.py \
  novaic-cortex/tests/test_pr234_control_stack.py

13 passed in 0.34s
```

## Known Gaps

- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py` and `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` still contain stale comments/docstrings saying `ContextEngine`, `DFS push`, `DFS pop`, or "may compact". These are comment/docstring residue, not live old execution.
- `Workspace.read_context()` and `/v1/context/read` still expose materialized `context.jsonl` projection for inspection/debug. `handle_context_read()` also reads this projection to de-duplicate environment notification hints before appending new notification events. This is live projection maintenance, but not the active LLM source.
- `/v1/internal/reindex` still uses archived `context.jsonl` and `summary.md` to extract human labels for archived scopes. This is history/index maintenance, not active LLM assembly.

## Artifacts

- This result file.
