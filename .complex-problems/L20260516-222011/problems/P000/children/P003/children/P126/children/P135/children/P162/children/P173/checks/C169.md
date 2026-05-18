# Context read handler residue classification check

## Summary

`P173` is solved. The context-read handler is classified as active-safe for explicit context inspection and environment notification hints, not provider-message authority. The one-go result is accepted because source mapping plus focused context-read and prepare-context guard tests directly cover the risk.

## Evidence

- Handler registration: `novaic-agent-runtime/task_queue/handlers/context_handlers.py:81`.
- Projection read: `context_handlers.py:103-104`.
- Notification idempotency and hint append: `context_handlers.py:106-160`.
- Return shape: `context_handlers.py:168-174`.
- Tests: context-read by-id/order tests and prepare-context authority guard tests passed with `31 passed`.

## Criteria Map

- Handler mapped with line pointers: satisfied.
- Role classified: active-safe inspection/notification-hint side path.
- Context-read tests identified/run: satisfied.
- Provider-authority usage fixed/split: no provider-authority use found; prepare/LLM guards prove exclusion.

## Execution Map

- `T160` one-go executed after parent residue classification split.
- Recorded result `R155`.

## Stress Test

If context-read starts fetching message bodies or scanning UI message rows, by-id/order tests fail. If prepare context starts using legacy `context.read` projection as provider messages, PR-85 guardrail tests fail.

## Residual Risk

- Other runtime call sites remain for sibling inventory `P175`.

## Result IDs

- R155
