# Cortex prepare_for_llm read-model authority success check

## Summary

Success. `R135` proves the Cortex prepare endpoint is ContextEvent/read-model backed and not `context.jsonl` backed.

## Evidence

- Endpoint: `api.py:925-946`.
- Read model: `context_event_read_model.py:66-117`.
- Source scan: `read_context` appears in `/v1/context/read`, not in `context_prepare_for_llm`.
- Tests: `33 passed in 0.09s`.

## Criteria Map

- Endpoint/helper pointers mapped: satisfied.
- `prepare_context`/read-model used: satisfied by endpoint constructing `ContextEventReadModel(...).prepare()`.
- `read_context` not called by endpoint: satisfied by source scan.

## Execution Map

- One-go leaf inspected source and ran focused read-model/projection suites.

## Stress Test

- Read-model tests include empty-root reset/closed cases, projection replay, and budget behavior, which exercise authority over event streams rather than materialized context files.

## Residual Risk

- Non-blocking for P156: runtime caller and static guard are separate siblings.

## Result IDs

- `R135`
