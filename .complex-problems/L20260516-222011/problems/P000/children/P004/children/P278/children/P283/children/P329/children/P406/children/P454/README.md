# Aggregate compatibility focused behavior tests

## Problem

Final compatibility verification needs focused behavior tests around attach, finalize, session-ended, recovery, archive, context, shell, and compatibility guards.

## Success Criteria

- Run focused runtime tests for attach/finalize/session-ended/recovery/session-state/generation guards.
- Run focused Cortex tests for archive/context/event/payload/shell compatibility guards.
- Save logs and exit statuses.
- Spawn repair if any suite fails.
