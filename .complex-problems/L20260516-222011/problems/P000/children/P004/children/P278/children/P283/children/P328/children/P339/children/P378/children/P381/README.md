# Runtime focused finalize regression tests

## Problem

The runtime finalize/session-ended generation boundary needs a focused pytest pass covering the actual state mutation and outbox/recovery paths.

## Success Criteria

- Focused runtime modules compile successfully.
- Focused runtime pytest suites for finalize ownership, session FSM, recovery, outbox cutover, attach/dispatch, and compensation pass.
- Any failing or missing runtime test is fixed or split into a follow-up problem.
- The result records exact commands and outcomes.
