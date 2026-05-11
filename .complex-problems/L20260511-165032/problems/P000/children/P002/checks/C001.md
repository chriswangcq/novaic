# Queue FSM Saga session adapter audit check

## Summary

Audit succeeded for this boundary: the primary session path is on the session-ledger/outbox route, and the remaining live bypass surface is explicitly identified as unrestricted generic saga creation.

## Evidence

- `R001` inspected session repository, session outbox, observed event handler, saga repo, saga trigger handler, and saga definitions.
- `SessionRepository` injects clock and scope-id providers and records wake intent through session outbox.
- `SessionOutboxDispatcher` is the intended wake saga creation boundary.
- `SagaTopics.SAGA_TRIGGER` and `/api/queue/sagas/create` can still create arbitrary saga types.

## Criteria Map

- `tq_session_state` authority checked: satisfied.
- Direct saga creation paths checked: satisfied; unrestricted generic creation remains.
- Finalize ownership checked: satisfied; required reason/generation/remaining_stack path exists.
- Hidden dependency boundary checked: partially satisfied; no urgent env/time/id issue found in session repo, but coordinator remains thick.

## Execution Map

- `T002` ran targeted source searches and code inspection.
- `R001` recorded clean boundaries and remaining bypass risk.

## Stress Test

If a stale component or operator publishes a `saga.trigger` task with `saga_type=subagent_wake`, the system can create a wake saga without session inbox/outbox coordination. The current app may not do that, but the live API/handler still permits it.

## Residual Risk

High for architecture hygiene, medium for immediate production probability. This should become an implementation ticket: restrict direct saga creation of session-owned sagas.
