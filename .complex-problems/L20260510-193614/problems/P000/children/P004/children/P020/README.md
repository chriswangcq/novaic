# Phase 3D Quarantine File-Walk Stack Authority

## Problem

After SQLite read cutover, `_collect_active_stack` and projection-file walking must not remain on runtime authority paths. If kept, they need a repair/debug name and explicit isolation.

## Success Criteria

- Runtime API paths no longer call file-walk active stack collection for authority decisions.
- Any remaining file-walk stack code is renamed or documented as repair/debug only.
- Tests or grep guards catch reintroduction of file-walk authority into `skill_begin`, `skill_end`, and default `context_status`.
- Old tests that assert file-walk authority are rewritten or deleted.
