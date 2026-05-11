# Live recovery verification check

## Summary

P008 is successful. Production is no longer wedged in active state, the repaired `agentctl` meta-read path works, and no recent post-deploy logs show the old failure signatures.

## Evidence

- `tq_session_state` shows the main agent session is `no_active`.
- Recent log scan returned `clean` for all checked runtime/Cortex/queue logs.
- Direct Cortex shell smoke returned `exit_code=0`.
- Cortex log confirms `/v1/meta/read` returned status `200` during the smoke.

## Criteria Map

- No new recurrence signatures -> satisfied by recent log scan.
- Shell capability no longer 401s -> satisfied by direct `agentctl im read --limit 1` smoke and Cortex `/v1/meta/read status=200`.
- Stale active session cleared -> satisfied by session state `no_active`.

## Execution Map

- `T008` / `R006` -> production DB/log inspection plus direct shell capability smoke.

## Stress Test

- If internal auth were still broken, the direct smoke would return stderr with `missing or invalid X-Internal-Key`.
- If step-ref projection or finalize compensation were actively failing after deploy, recent worker/Cortex logs would show the old signatures.
- If the old session were still wedged, `tq_session_state` would still show `active` with the old scope.

## Residual Risk

- A complete user-visible reply smoke depends on the external LLM path and was not forced here. The failure being repaired was earlier than model generation, and that earlier path is now verified.

## Result IDs

- R006

## Blocking Gaps

- none
