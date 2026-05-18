# Runtime bridge materialized context helper narrowing result

## Summary

Renamed runtime bridge materialized context helpers so their projection-only role is explicit. Production runtime code no longer calls broad `bridge.read_context`, `bridge.append_context`, or `bridge.append_context_batch` names.

## Done

- Renamed `CortexBridge.read_context` to `read_materialized_context_projection`.
- Renamed `CortexBridge.append_context` to `append_materialized_context_projection`.
- Renamed `CortexBridge.append_context_batch` to `append_materialized_context_projection_batch`.
- Updated runtime handlers and runtime tests to the new helper names.
- Fixed three stale test fixtures that lacked explicit positive `session_generation`; production validators were not loosened.

## Verification

Focused runtime suite:

```text
60 passed in 0.32s
```

Old helper-name guard:

```text
rg -n '\b(read_context|append_context|append_context_batch)\b' novaic-agent-runtime/task_queue novaic-agent-runtime/tests -g '*.py'
# no matches
```

Remaining runtime production helper names are explicitly projection-scoped:

```text
read_materialized_context_projection
append_materialized_context_projection
append_materialized_context_projection_batch
```

## Known Gaps

- P444 still needs to clarify the `context.read` task handler contract.
- P445 still needs Cortex endpoint/test cleanup and wording.

## Artifacts

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-agent-runtime/task_queue/handlers/context_handlers.py`
- `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
- Runtime tests updated under `novaic-agent-runtime/tests/`
- `.complex-problems/L20260516-222011/tmp/p443/runtime-materialized-context-focused-pytest.after-fix.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p443-before-rename-hits.txt`
- `.complex-problems/L20260516-222011/tmp/p443-after-rename-old-hits.txt`
