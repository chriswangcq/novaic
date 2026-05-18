# Projection production stale branch cleanup

## Problem

After inventory, stale production branches should be physically removed rather than carried as confusing fallback logic. Active or compatibility branches must remain only when justified by current call paths or persisted data.

## Success Criteria

- Remove production branches classified stale by the inventory.
- Keep active/compatibility branches only with a clear reason in the result.
- Do not introduce broad compatibility fallbacks or local-only fallbacks.
- Run focused production-side projection tests after edits.
