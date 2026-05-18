# Context task handler projection contract cleanup result

## Summary

Clarified runtime context handler contracts so `context.read` / `context.append` are described as materialized projection and notification hint maintenance, not LLM history assembly.

## Done

- Updated `task_queue/handlers/context_handlers.py` module docs, handler docstrings, and idempotency comments.
- Updated context-read test module docstrings to say notification projection hints/order.
- Kept behavior unchanged.

## Verification

Focused runtime tests:

```text
45 passed in 0.21s
```

Contract scan highlights:

```text
Context Handlers — Cortex materialized projection maintenance
This task is not the LLM history assembly path.
Append a materialized projection message OR write a durable step.
```

## Known Gaps

- P445 still needs Cortex endpoint/test cleanup and wording.

## Artifacts

- `novaic-agent-runtime/task_queue/handlers/context_handlers.py`
- `novaic-agent-runtime/tests/test_context_read_by_ids.py`
- `novaic-agent-runtime/tests/test_context_read_ordering.py`
- `.complex-problems/L20260516-222011/tmp/p444/context-handler-after-contract-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p444/runtime-context-contract-focused-pytest.with-status.txt`
