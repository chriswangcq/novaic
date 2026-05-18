# Runtime focused compatibility behavior tests

## Problem

Run the focused runtime behavior tests that prove the Queue/session harness uses the intended FSM/generation/finalize/outbox contracts rather than old imperative or compatibility paths.

## Success Criteria

- Run focused `novaic-agent-runtime` tests for attach, finalize, session-ended, recovery, session-state/generation, legacy cleanup, explicit contracts, historical image guard, and shell output contract.
- Save the exact command, exit status, and log under `.complex-problems/L20260516-222011/tmp/p456/`.
- If tests fail, create a repair follow-up with failing test names and first actionable traceback.
