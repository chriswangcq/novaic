# Phase 3B2 Skill Begin End Stack Writes

## Problem

Successful `skill_begin` and `skill_end` currently return file-walk stacks but do not update operational SQLite active-stack projection. Runtime reads cannot cut over safely until begin/end writes are authoritative.

## Success Criteria

- Successful `skill_begin` writes the pushed stack to operational SQLite after child scope creation/event append.
- Successful `skill_end` writes the popped stack to operational SQLite after child close/event append.
- Error branches do not mutate SQLite stack projection.
- Tests cover nested begin/end projection state and restart-like store reuse.
