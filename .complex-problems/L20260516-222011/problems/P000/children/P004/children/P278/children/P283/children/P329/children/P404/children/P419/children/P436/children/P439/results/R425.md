# Context endpoint ownership and migration result

## Summary

Closed materialized context endpoint ownership cleanup through four child problems. The endpoints remain because they have current projection/notification owners, but runtime bridge names and docs/tests now make their projection-only role explicit and P438 proves they are not authoritative LLM prepare history.

## Done

- `P442` / `R421` / `C447`: classified all materialized context projection owners.
- `P443` / `R422` / `C448`: renamed runtime bridge helpers from broad `read_context/append_context/append_context_batch` to explicit materialized projection names.
- `P444` / `R423` / `C449`: clarified runtime context task handler contract as projection/notification maintenance, not LLM history assembly.
- `P445` / `R424` / `C450`: clarified Cortex endpoint/test wording for `/v1/context/read|append|batch`.

## Verification

- Runtime materialized context focused tests: `60 passed`.
- Runtime context contract focused tests: `45 passed`.
- Cortex context endpoint focused tests: `27 passed`.
- Old runtime broad helper name scan has no matches in `novaic-agent-runtime/task_queue` or `novaic-agent-runtime/tests`.

## Known Gaps

- None inside P439. Final aggregate bridge guard remains P440.

## Artifacts

- Child results/checks: `R421/C447`, `R422/C448`, `R423/C449`, `R424/C450`.
- Runtime changed files:
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - `novaic-agent-runtime/task_queue/handlers/context_handlers.py`
  - `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
  - related runtime tests.
- Cortex changed files:
  - `novaic-cortex/novaic_cortex/api.py`
  - `novaic-cortex/tests/test_context_event_api_context_writes.py`
  - `novaic-cortex/tests/test_pr67_wake_child_api.py`
