# Runtime compatibility cleanup ticket

## Problem Definition

The inventory found runtime-side compatibility/defaulting hits in Queue/session/task code. Some are likely safe counters or generic FSM infrastructure, but any live attach/finalize/session-ended/recovery path that defaults or infers generation must be removed or converted to explicit validation.

## Proposed Solution

Use the `P402` guard outputs to audit runtime hits in small slices:

1. Inspect session authority paths: `session_repo.py`, `session_fsm.py`, `session_outbox.py`, `session_recovery.py`, `session_ledger.py`, `session_observed_events.py`, and `queue_audit.py`.
2. Inspect generic Queue infrastructure hits: `queue_db.py`, `saga_repo.py`, `task_fsm.py`, and generic FSM state/event projections.
3. Inspect task/saga/contract hits: `react_think.py`, `react_actions.py`, `wake_finalize.py`, `subagent_wake.py`, and session/Cortex handlers.
4. Inspect worker/health retry/counter hits and classify them as non-session-authority or patch if they influence session mutation.
5. Patch any dangerous live path with explicit generation validators or typed contracts.
6. Add focused regression tests for changed live paths.
7. Rerun runtime guards and focused tests.

## Acceptance Criteria

- Every runtime hit from `P402` is classified as fixed, safe validator/test, safe counter/projection, or generic non-session-authority infrastructure.
- Dangerous runtime generation/default compatibility residue is removed.
- Changed live runtime boundaries have focused tests.
- Runtime guard searches have no unclassified live attach/finalize/session-ended generation residue.
- Runtime-focused tests pass.

## Verification Plan

- Reuse `P402` guard outputs and rerun runtime-specific guards after changes.
- Run focused runtime pytest suites for session repository/FSM/outbox/recovery/handlers/contracts and any patched generic Queue components.
- Include source guard output in the result or final child verification.

## Risks

- Some `generation` fields in `queue_db.py` / `saga_repo.py` are generic FSM infrastructure rather than session generation; over-cleaning could break valid generic state mechanics.
- Some round/retry/counter defaults are harmless but noisy; they need explicit classification, not deletion by regex.
- Runtime cleanup can touch many files; split by responsibility boundary before editing.

## Assumptions

- No backward compatibility is required for missing/stale session generation in live session paths.
- Generic non-session FSM generations may remain if classified and tested as infrastructure state rather than session-generation authority.
