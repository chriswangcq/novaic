# Runtime finalize generation aggregate regression

## Problem

Runtime finalize/session-ended behavior needs a focused aggregate regression pass after targeted fixes. The pass must prove repository, FSM, outbox, handler, recovery, watchdog, restart, and pending-input paths reject stale or missing generation and cannot mutate a newer active session.

## Success Criteria

- Focused runtime pytest suites covering finalize ownership, session FSM, outbox cutover, recovery/watchdog, restart/pending input, attach/finalize generation checks, and legacy cleanup pass.
- Runtime source guards for missing generation, bool generation coercion, direct active clearing, and fallback generation behavior are run and classified.
- Any unsafe runtime hit is fixed or converted into a follow-up problem.
- The result records exact commands, pass/fail counts, and residual risks.
