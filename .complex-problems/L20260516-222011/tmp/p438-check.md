# Check: P438 agent loop prepare-path proof

## Verdict

Success.

## Evidence Reviewed

- Result `R420`
- Runtime focused tests: `29 passed`
- Cortex focused tests: `15 passed`
- Runtime guard test poisoning `read_context` while asserting prepared snapshot wins.
- Cortex source guard confirming `prepare_for_llm` has no `read_context` fallback.

## Criteria Map

- Live LLM messages come from `bridge.prepare_for_llm`: satisfied.
- Cortex prepare endpoint uses ContextEvent read model: satisfied.
- Runtime tests prove `read_context` is not LLM prepare source: satisfied.
- Bypass discovered/fixed/split: no bypass found; context endpoint ownership remains P439 by design.

## Execution Map

The proof follows the actual saga path rather than just checking helper names: `react_think` schedules `CORTEX_PREPARE_LLM_CONTEXT`, the handler calls `prepare_for_llm`, and the LLM call consumes the assembled snapshot.

## Stress Test

The key regression injects an explicit stale `read_context` value and verifies it does not enter the final LLM message list. This directly targets the feared old-projection bypass.

## Residual Risk

Materialized context endpoints still exist and are live for non-prepare surfaces; P439 owns their cleanup/ownership decision.
