# Session-ended outbox delivery generation contract check

## Summary

Success. P336's direct session-ended delivery contract is now explicit and fail-closed for generation identity. I checked the possible "saga identity" ambiguity too: saga identity is owned by task metadata in the saga task runner, while the handler payload carries the explicit downstream finalize identity (`agent_id`, `subagent_id`, `scope_id`, positive `generation`, `finalize_reason`, `remaining_stack`). That is sufficient for this generation-contract problem, with upstream react defaults intentionally left to P337/P339.

## Evidence

- P340/R322 maps the delivery chain from wake-finalize payload builder to handler, SagaClient, route, and repository.
- P341/R323 removes wake-finalize `session_generation or 0` and adds missing/zero-generation rejection tests.
- P342/R324 enforces positive generation at handler, SagaClient, and route schema.
- P343/R328 verifies direct residue cleanup and classifies upstream react defaults.
- P344/R329 runs aggregate verification: `40 passed in 0.44s`.
- `task_queue/workers/task_execution.py` uses `task["saga_id"]` and `step_name` to resolve saga steps before calling the real handler; session-ended handler payload does not need to duplicate saga id to protect the downstream session mutation boundary.

## Criteria Map

- Map session-ended/finalize outbox effect builders, payload schemas, and delivery handlers: satisfied by P340.
- Verify payloads include expected saga/scope/generation and finalize reason where required: satisfied. Saga identity is task metadata for saga step execution; downstream payload carries required scope, positive generation, finalize reason, and remaining stack.
- Ensure missing expected generation or scope is rejected before publish/delivery: satisfied. Missing/zero generation fails in wake-finalize payload construction, handler, client, route, and repository; missing scope remains handler-required.
- Add tests proving outbox delivery preserves generation identity and rejects malformed finalize/session-ended effects: satisfied by P341/P342 tests and P344 aggregate verification.
- Remove stale compat behavior that silently fills missing generation from current state: satisfied for direct session-ended delivery. Upstream react defaults are classified as broader follow-on work, not accepted delivery compatibility.

## Execution Map

- Producer boundary: `wake_finalize.py`.
- Handler boundary: `session_handlers.py`.
- Transport boundary: `SagaClient.session_ended`.
- API boundary: `SessionEndedRequest`.
- Mutation boundary: `SessionRepository.session_ended` and pure session FSM.
- Aggregate verification: P344/R329.

## Stress Test

- Checked the common partial-migration failure: new validation exists but old fallback remains. Direct source guards are clean.
- Checked malformed zero generation from upstream. It now fails closed before accepted `session.ended` delivery.
- Checked valid positive generation still passes through existing finalize/restart tests.

## Residual Risk

- Upstream `react_think.py` and `react_actions.py` still default missing `session_generation` to `0`. This is not a P336 accepted-delivery gap after P341/P342, but it is real architecture residue for P337/P339 and must be removed there.
- Saga id is not duplicated into the handler payload; it is carried by task metadata. If future audit wants handler-level saga-id validation, that should be a distinct provenance/idempotency problem rather than part of the generation-contract closure.

## Result IDs

- R330
