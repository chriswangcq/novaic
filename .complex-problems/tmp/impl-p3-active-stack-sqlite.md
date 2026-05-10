# Phase 3 Active Stack And Status SQLite Cutover

## Problem

Runtime active stack/status still reads projection files. Switch control stack authority to SQLite projection.

## Success Criteria

- `skill_begin`, `skill_end`, and `context_status` read/write stack projection from SQLite.
- Projection-file walking is removed from the runtime authority path or isolated as repair/debug only.
- Tests cover nesting, mismatch, finalize/open-child behavior, restart recovery, and old path residue.

