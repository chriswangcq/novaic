# PR-325 Worker Policies And Metrics

Status: Closed
Phase: 1
Owner: Codex

## Goal

Make retry/backoff/metrics/logging hooks explicit in the component substrate.

## Scope

- Add minimal worker metrics snapshot.
- Add explicit policy/config objects for poll interval, max idle sleep, and
  exception handling.
- Keep policy objects independent of business state.

## Deletion Target

None in this ticket.

## Acceptance

- Metrics count polls, handled jobs, successes, failures, empty polls, and loop
  errors.
- Policies are passed explicitly.
- Tests can control time and sleep.

## Verification

- Unit tests for metrics and policy validation.

## Closure Notes

Closed. Added `queue_service/worker/policies.py` with explicit runtime ports,
config validation, shutdown controller, and metrics. Verified with
`tests/test_pr325_worker_policies_and_metrics.py`.
