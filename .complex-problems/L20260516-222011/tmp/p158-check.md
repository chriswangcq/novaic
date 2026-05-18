# LLM prepare authority residue guard success check

## Summary

`P158` is solved by `R137`. The problem asked for durable guard coverage preventing `context.jsonl`/`read_context` authority from returning to the LLM prepare path. The result adds behavior and static tests that would fail if final LLM messages were sourced from `context.read` or if the final `llm.call` handler directly used `read_context`.

## Evidence

- Behavioral guard: `test_prepare_llm_context_uses_prepare_snapshot_not_context_read_projection` creates conflicting `context.read` and `prepare_for_llm` outputs and verifies only `prepare_for_llm` reaches final messages.
- Static prepare guard: `test_prepare_llm_context_static_authority_contract` requires `prepare_for_llm`/`CortexPreparedContext` assembly and forbids `read_result.context` assembly.
- Final LLM handler guard: `test_llm_call_handler_does_not_read_cortex_context_as_authority` forbids direct `read_context`/`context.read` in `llm_handlers`.
- Stale source residue reduced: `react_think` no longer says the think phase reads `context.jsonl` for LLM context assembly.
- Verification passed with `29 passed` across prepare smoke guards, explicit runtime contracts, and runtime tool path contracts.

## Criteria Map

- Existing guard coverage is identified or a new guard is added: satisfied by the three named tests above.
- Guard fails if LLM prepare assembly starts using `read_context`/`context/read` as authority: satisfied by the conflicting-snapshot behavior test and static source guard.
- Focused tests pass: satisfied by the `pytest` command recorded in `R137`.

## Execution Map

- `R137` implemented the missing static guard and classified all remaining search hits.
- No child or follow-up problem was required because remaining `context.read` usage is limited to notification hinting, API bridge, topics, and tests.

## Stress Test

- Simulated stale projection pressure: `context.read` returns `"legacy context.read projection"` while `prepare_for_llm` returns `"prepared read-model snapshot"`. The final assembled LLM messages reject the stale projection.
- Simulated future source regression: if someone wires `read_result.get("context")` into prepare assembly, the static guard fails.
- Simulated final-handler regression: if `llm_handlers` starts calling `read_context` directly, the explicit contract test fails.

## Residual Risk

- The topic name `context.read` is still confusing because it now means notification-hint/idempotency projection, not final LLM authority. This is non-blocking for the current problem because guard coverage isolates it from provider-message assembly.
- A future rename of `context.read` could improve clarity, but it is a separate API cleanup problem rather than an authority-boundary defect.

## Result IDs

- R137
