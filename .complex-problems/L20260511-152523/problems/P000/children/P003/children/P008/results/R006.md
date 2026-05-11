# Live recovery verification result

## Summary

Verified production after deployment. The previously stuck session is no longer active, post-deploy recent logs are clean for the three old signatures, and direct Cortex shell capability smoke succeeds.

## Done

- Queried production `tq_session_state`.
- Scanned recent post-deploy worker/Cortex/queue logs for old recurrence signatures.
- Ran direct production `/v1/internal/shell` smoke with `agentctl im read --limit 1`, explicitly exercising `agentctl` plus Cortex `/v1/meta/read`.

## Verification

- Session state:
  - `822af016-31a1-49bb-b529-9b8f539a0831:main-822af016|no_active|9|||2026-05-11T08:00:10.877Z|`
  - This means the old active wedge has been cleared to `no_active`.
- Recent signature scan over worker/Cortex/queue logs:
  - `task-worker-control-1.log`: clean
  - `task-worker-control-2.log`: clean
  - `task-worker-execution-1.log`: clean
  - `task-worker-execution-2.log`: clean
  - `cortex.log`: clean
  - `queue-service.log`: clean
- Direct shell capability smoke:
  - `/v1/internal/shell` returned `exit_code=0`.
  - `stdout` was `{"success": true, "messages": [], "count": 0}`.
  - Cortex log showed `/v1/meta/read status=200` and `sandbox.exec cmd='agentctl im read --limit 1' exit_code=0`.

## Known Gaps

- The latest saga table still contains the historical failed sagas from before deploy; they are not active and match the pre-fix timestamps.
- This smoke validates the repaired shell/meta path and stale-session cleanup state, but it is not a full UI-to-LLM provider reply test.

## Artifacts

- Production queue DB query output.
- Production log signature scan output.
- Production direct shell smoke output.
