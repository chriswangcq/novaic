# Session-ended handler client route contract check

## Summary

Success. The one-go result is acceptable because it hardened all three delivery surfaces named by the problem: handler, live Saga client, and route schema. The check also caught and corrected a mistaken assumption in the ticket wording: `session_ended(...)` is on `SagaClient`, not `TaskQueueClient`.

## Evidence

- `task_queue/handlers/session_handlers.py` now validates `generation` through `_positive_generation(...)`, rejecting missing, bool, non-castable, zero, and negative generation before client delivery.
- `task_queue/client.py::SagaClient.session_ended(...)` now calls `_require_positive_generation(...)` before `_request(...)`.
- `queue_service/routes.py::SessionEndedRequest` now declares `generation: int = Field(gt=0)`.
- `tests/test_pr254_finalize_ownership.py` verifies handler rejection, no extra client call after invalid handler input, SagaClient request prevention for zero generation, route model rejection, and valid payload preservation.
- Focused verification passed: `9 passed in 0.21s`.
- Broader finalize/session suite passed: `25 passed in 0.32s`.
- Source guard for handler's old `if generation is None`-only validation is clean.

## Criteria Map

- Handler rejects missing, zero, negative, or non-castable generation before client delivery: satisfied.
- Client rejects non-positive generation before HTTP request: satisfied on the actual live client class, `SagaClient`.
- Queue-service route schema rejects non-positive generation: satisfied via `Field(gt=0)`.
- Existing valid finalize delivery tests still pass: satisfied.
- Focused tests cover handler, client, and route validation: satisfied.

## Execution Map

- Handler boundary: payload validation fails before `saga_client.session_ended(...)`.
- Client boundary: invalid generation fails before `_request("POST", "/api/queue/session-ended", ...)`.
- API boundary: Pydantic route request rejects `generation <= 0`.
- Repository boundary remains the downstream fail-closed guard from P335.

## Stress Test

- Invalid handler payload with `generation=0` now raises and does not append a second fake-client call.
- Invalid SagaClient call with `generation=0` now raises and does not call `_request`.
- Invalid route model with `generation=0` now raises `PydanticValidationError`.
- Valid `generation=1` still flows through client and route.

## Residual Risk

- Non-blocking for P342: upstream react contracts can still default `session_generation` to zero, but P341 and P342 now reject that before repository mutation. Broader cleanup remains P343/P337/P339.
- Non-blocking for P342: Pydantic may coerce numeric strings before validation; this is acceptable at the HTTP schema boundary because positive generation semantics are preserved.

## Result IDs

- R324
