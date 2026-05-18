# Audit ContextEvent pure projection

## Problem Definition

`project_context_events` is the pure function that turns ordered ContextEvents into LLM-facing messages and stack frames. Its invariants and event handlers must be mapped and tested before deeper display/payload projection work changes nearby behavior.

## Proposed Solution

Inspect `novaic-cortex/novaic_cortex/context_event_projection.py` and `novaic-cortex/tests/test_context_event_projection.py`. Record:

- Snapshot shape and token estimate behavior.
- Stream/root/sequence replay validation.
- Event handlers for root, wake, archived wake, system prompt, context message, notification, skill open/close, assistant tool call, and tool result.
- Scope message routing, stale wake/sibling suppression, folded summaries, and LIFO enforcement.
- Tool result content selection and metadata: `step_ref`, `payload_ref`, orphan marking, stable lookup ref.

Run the projection tests. If an active projection issue is found, fix it if narrow; otherwise spawn a focused runtime child problem.

## Acceptance Criteria

- Result maps all projection invariants and event handlers with source pointers.
- Result explains `step_ref`, `payload_ref`, orphan tool result marking, folded summaries, and notification hints.
- Projection tests are run and evidence recorded.
- Any discovered issue is fixed or split.

## Verification Plan

- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_projection.py`

## Risks

- This ticket should not decide final display/base64 projection behavior; it only covers ContextEvent pure projection.
- Tool result content selection may intentionally use preview/summary/head; deeper shell/display formatting is owned by sibling projection problems.

## Assumptions

- `project_context_events` is pure and should remain deterministic from its event list.
- Provider-native media assembly is not performed in this layer.
