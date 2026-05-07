# PR-286D2 — Pending Wake Caller Metrics

Status: Closed

## Goal

Update callers that log or count `saga_started` to also treat pending wake
contracts as successful durable dispatch acknowledgements.

## Scope

- Scheduler worker logs/metrics.
- Any common assembler tests that classify pending wake result.
- Avoid implying a live saga id exists when Queue only returned queued outbox
  acceptance.

## Dependencies

- PR-286D1.
- PR-293.

## Acceptance Criteria

- Pending wake is logged as queued, not unexpected.
- No caller assumes `saga_id` is present for pending wake actions.

## Verification

- Scheduler/assembler tests.

## Closure Notes

- Scheduler dispatch handling now treats pending wake contracts as successful
  queued acknowledgements and records `dispatch_queued` separately from
  immediate attach/start.
- Tests cover queued dispatch classification without requiring an immediate
  `saga_id`.
- Verified by `tests/test_scheduler_dispatch.py` and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
