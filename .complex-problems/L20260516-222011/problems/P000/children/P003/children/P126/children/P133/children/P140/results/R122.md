# ContextEvent read model and budget boundary audit result

## Summary

Completed the read-model audit. One test gap was found and fixed: empty `root_scope_path` behavior was implemented but untested. Added a focused regression test. No production code change was required.

## Done

- Mapped prepared context shape and status:
  - `novaic-cortex/novaic_cortex/context_event_read_model.py:30-53`
  - `ContextEventPreparedContext.status()` reports stack depth, current skill, frames, message count, token estimate, usage ratio, and executing/closed phase.
- Mapped reset boundary:
  - `context_event_read_model.py:56-63`
  - `ContextEventReadModelResetRequired` is raised when a non-empty root has no event stream.
- Mapped constructor dependencies:
  - `context_event_read_model.py:69-82`
  - Workspace, root path, compaction config, token counter, and optional injected event store are explicit.
- Mapped prepare flow:
  - `context_event_read_model.py:84-117`
  - Empty root path returns an empty closed prepared context.
  - Non-empty root reads ContextEvents from the event store.
  - Missing event stream raises reset-required; there is no silent legacy fallback.
  - Events are projected through `project_context_events`.
  - Projected messages pass through `budget_compact`.
  - Estimated tokens and usage ratio are calculated after compaction.
  - Stack is normalized top-first.
- Mapped stack normalization:
  - `context_event_read_model.py:120-129`
  - Reverses projection stack so current frame is first and adds `skill_name="wake"` for wake frames.
- Added test:
  - `novaic-cortex/tests/test_context_event_read_model.py`
  - `test_event_read_model_empty_root_path_returns_closed_empty_context`

## Verification

- Focused read-model test:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_read_model.py
```

Result:

```text
4 passed in 0.09s
```

- ContextEvent stack regression bundle:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_projection.py novaic-cortex/tests/test_context_event_store.py novaic-cortex/tests/test_context_event_read_model.py
```

Result:

```text
49 passed in 0.16s
```

- Static sweep:
  - `rg` confirmed `ContextEventReadModel.prepare` uses `budget_compact`, `ContextEventReadModelResetRequired`, and `_top_first_stack`.
  - `rg` also shows old `context.jsonl` append helpers exist in `workspace.py`, but this read-model layer does not read them; workspace materialized projections are covered by sibling problem P134.

## Known Gaps

- Workspace materialized `context.jsonl` helpers are intentionally out of scope and tracked by sibling problem P134.
- Runtime prepare-context handler wiring is intentionally out of scope and tracked by sibling problem P135.

## Artifacts

- Source: `novaic-cortex/novaic_cortex/context_event_read_model.py`
- Test changed: `novaic-cortex/tests/test_context_event_read_model.py`
