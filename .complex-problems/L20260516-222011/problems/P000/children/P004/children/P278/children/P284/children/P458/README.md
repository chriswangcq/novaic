# Session outbox effect inventory

## Problem

Map session outbox effect types, creation points, persistence points, workers, and downstream handlers with file references.

## Success Criteria

- List every session outbox effect type and payload identity fields.
- Map where effects are recorded and where they are delivered.
- Identify downstream handler boundaries for wake saga creation, attach input, session-ended/finalize, recovery/archive, and observed wake-created updates.
- Save source guard artifacts under `.complex-problems/L20260516-222011/tmp/p458/`.
