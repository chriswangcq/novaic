# Cortex Stable Workspace Path Contract Audit

## Problem

Agents should use `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW`, not copied `novaic-cortex-sandbox-*` backing paths. Stable path guidance and runtime guards must be visible and tested.

## Success Criteria

- Inspect shell schema/help/docs for stable path guidance.
- Verify runtime rejects or discourages stale backing paths.
- Run focused runtime/Cortex path abuse tests.
- Fix bounded guidance or guard gaps found.
