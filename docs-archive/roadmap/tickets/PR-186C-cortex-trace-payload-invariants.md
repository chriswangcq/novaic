# PR-186C — Cortex Trace and Payload Invariant Acceptance

Status: `[closed]` — 2026-05-03

## Analysis

Cortex already projects reasoning/action/observation/summary records and keeps raw payload behind explicit payload refs. Payload read/search/summarize/qa are explicit tools.

The gap is one acceptance guard covering the final product invariant: active scopes can expose work trace, closed scopes expose summaries, and default trace projection never leaks raw payload refs or transport debug fields.

## Scope

- Add Cortex acceptance tests for trace projection, closed-scope folding, and payload ref privacy.
- Guard that explicit payload interpretation is the only summary/QA path for payloads.
- Guard that structural scope close does not synthesize durable memory.

## Tests

- Cortex targeted pytest for trace/payload/scope acceptance.
- Cortex full pytest before closure.

## Deployment / Git

- If only tests/docs change: no Cortex deploy required.
- If Cortex behavior changes: deploy Cortex and record smoke evidence.

## Closure

- Added `tests/test_pr186_trace_payload_acceptance.py`.
- Covered active trace projection as reasoning/action/observation, raw payload privacy, and closed scope projection as summary-only.
- Tests:
  - `PYTHONPATH=. pytest -q tests/test_pr186_trace_payload_acceptance.py` → `2 passed`
  - `PYTHONPATH=. pytest -q` → `402 passed, 16 skipped`
- No Cortex deploy required; no behavior changed.
