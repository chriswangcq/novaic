# Check: Session generation lifecycle and advancement inventory

## Summary

Success. This was a one-go audit, so I checked it strictly: R314 maps lifecycle creation, advancement, activation, rebuild, tests, and suspicious defaults. The original P326 criterion allows hidden paths to be flagged rather than fixed in this slice, and R314 explicitly flags both discovered suspicious paths for the proper downstream child audits.

## Evidence

- R314 maps `tq_session_state.generation` as the active generation authority through `SessionLedgerRepository`.
- R314 maps allocation through `SessionLedgerRepository.next_generation(...)` and `SessionRepository` start/restart paths.
- R314 maps activation through `session_wake_plan.py`, `session_effects.py`, and `session_observed_events.py`.
- R314 maps rebuild through `session_rebuild.py` and flags `context.get("session_generation") or 1`.
- R314 ran focused lifecycle tests: `22 passed`.

## Criteria Map

- File-reference every generation creation/advancement path: satisfied by R314 for ledger, repo start/restart, wake plan/effect, observed activation, rebuild, and tests.
- Explain authoritative storage location: satisfied; `tq_session_state.generation` through `SessionLedgerRepository`.
- Identify whether generation changes are transactionally tied to session state transition: satisfied; start/restart allocation paths and observed activation are mapped, including global transaction boundaries.
- Flag or fix hidden generation path: satisfied by flagging rebuild fallback and attach-specific `active_generation(...)` behavior for P329/P327 respectively.

## Execution Map

- T318 executed bounded source inventory and focused test verification.
- No code changes were made in this ticket.

## Stress Test

- Hidden default risk: searched `or 1`, `or 0`, generation lifecycle helpers, and found the rebuild fallback.
- Missing enforcement risk: included wake-created observation tests and final residue guard tests in the focused run.
- Cross-boundary loss risk: checked wake plan/effect propagation of session generation into outbox/saga context.

## Residual Risk

- Non-blocking for P326: `session_rebuild.py` fallback still needs classification/removal in P329, and attach stale-scope generation behavior still needs classification in P327. Those are already explicit sibling child problems under P283.

## Result IDs

- R314
