# Production Runtime Topology Verified

## Summary

Verified that the deployed production backend is running the expected services and runtime worker roster after the `./deploy services` restart.

## Done

- Ran `./deploy status`.
- Ran local runtime roster command from `novaic-agent-runtime/scripts/runtime_worker_roster.py`.
- Ran `./deploy fresh-smoke`.
- Compared observed worker counts with code-defined role-level roster.

## Verification

- `./deploy status` passed:
  - Services bound: entangled, gateway, business, device, queue-svc, blob-service, cortex.
  - Runtime workers matched expected counts:
    - `task-worker control`: 2/2
    - `task-worker execution`: 2/2
    - `saga-worker`: 2/2
    - `session-outbox-worker`: 1/1
    - `saga-outbox-worker`: 1/1
    - `health`: 1/1
    - `scheduler`: 1/1
    - `subscriber`: 1/1
  - Relay reported active.
- Local roster command output matched the same role-level expectations.
- `./deploy fresh-smoke` passed for all required logs, including every runtime worker log and `subscriber.log`.

## Known Gaps

None.

## Artifacts

- `./deploy status` output.
- `./deploy fresh-smoke` output.
- `novaic-agent-runtime/scripts/runtime_worker_roster.py process-checks` output.
