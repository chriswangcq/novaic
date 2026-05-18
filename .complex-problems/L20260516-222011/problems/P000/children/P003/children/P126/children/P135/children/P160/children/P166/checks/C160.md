# Cortex prepare handler response shape map success check

## Summary

`P166` is successful. `R146` maps the handler source and proves the dangerous fallback path is guarded: `handle_context_read` contributes only notification `new_messages`, while final provider messages come from `CortexPreparedContext` returned by `bridge.prepare_for_llm`.

## Evidence

- `cortex_handlers.py:296-356` maps payload parsing, context-read notification ingestion, prepare call, tool loading, warning handling, assembly, and output return.
- `llm_assembly.py:115-139` maps final output fields.
- `llm_assembly.py:233-273` maps final message construction from `cortex_context.messages`, stack, warning, and tool schemas.
- Tests passed with `31 passed`.
- Existing guards prove `read_result.context` is not used as provider authority and a conflicting `context.read` projection does not enter final messages.

## Criteria Map

- Handler mapped with line pointers: satisfied by `R146`.
- `read_context`/local continuity use classified: satisfied; `handle_context_read` is active-safe notification-hint ingestion, not provider-message authority.
- Handler tests identified/run or guard added: satisfied by focused test suite and existing static/behavior guards.

## Execution Map

- `T151` executed as one-go after parent split to the handler leaf.
- No code changes were required because guard coverage already existed and passed.

## Stress Test

- Plausible failure: legacy `context.read` projection becomes provider-message authority. Existing test `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection` simulates exactly that conflict.
- Plausible failure: missing Cortex stack causes fallback to local context. Existing test rejects missing stack instead of falling back.

## Residual Risk

- No blocking residual risk for handler response shape. Bridge endpoint details remain with sibling `P167`.

## Result IDs

- R146
