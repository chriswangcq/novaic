# Context read handler residue classified

## Summary

Classified `handle_context_read` as an active-safe explicit context inspection / notification-hint handler, not an LLM provider-message authority path. It reads Cortex context, appends environment notification hints from scope meta `input_message_ids`, and returns `context` plus `new_messages`; prepare/LLM guard tests prove this output does not become provider messages.

## Done

- Mapped topic registration at `novaic-agent-runtime/task_queue/handlers/context_handlers.py:81`.
- Mapped payload extraction and validation at `context_handlers.py:91-101`.
- Mapped Cortex projection read at `context_handlers.py:103-104`.
- Mapped idempotency and notification-hint assembly from `input_message_ids` at `context_handlers.py:106-160`.
- Mapped output fields at `context_handlers.py:168-174`.
- Classified handler as active-safe side path: it can append environment notification hints to Cortex context and return `context`, but prepare handler tests prove provider messages come from `bridge.prepare_for_llm`, not this `context`.

## Verification

- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/test_context_read_by_ids.py novaic-agent-runtime/tests/test_context_read_ordering.py novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
- Result: `31 passed in 0.17s`.

## Known Gaps

- Broader caller inventory remains sibling `P175`.

## Artifacts

- No code changes were required for this leaf.
