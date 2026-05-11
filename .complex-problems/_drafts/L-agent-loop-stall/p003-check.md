# Deploy and verify check

## Summary

P003 is successful: the repaired code is deployed, services are healthy, the old active-session wedge is cleared, and the exact broken shell/meta path now succeeds.

## Evidence

- `./deploy services` and fresh-smoke completed successfully.
- `./deploy status` reported all backend services/workers healthy.
- `tq_session_state` shows `no_active` for the affected main agent session.
- Direct production shell smoke returned `exit_code=0` and Cortex logged `/v1/meta/read status=200`.
- Recent log scan returned `clean` for the known old signatures.

## Criteria Map

- Backend deployment complete -> satisfied by `R005`.
- Fresh services/workers healthy -> satisfied by `R005`.
- Stale active session cleared -> satisfied by `R006`.
- Repaired shell/context/finalize signatures absent -> satisfied by `R006`.

## Execution Map

- `T006` / `R007` -> aggregate result from deploy (`R005`) and live verification (`R006`).

## Stress Test

- If deployment missed runtime/Cortex changes, direct shell smoke or logs would still show the internal-key failure.
- If finalize/recovery remained broken, session state would still be active or recent logs would show the root-scope error.

## Residual Risk

- Historical failed saga rows remain in DB as audit history; they are pre-deploy and no longer active.

## Result IDs

- R007

## Blocking Gaps

- none
