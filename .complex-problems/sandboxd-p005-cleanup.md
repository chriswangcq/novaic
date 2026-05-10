# Remove stale in-process sandbox execution residue

## Problem

After sandboxd is the active server path, stale old-path helpers and compatibility branches must be removed or explicitly scoped as test adapters. This prevents future agents from accidentally reconnecting the old logic.

## Success Criteria

- Searches for old sandbox execution modules/classes and Cortex command wrapping residue find no active production path.
- Any remaining direct runner is named/documented as a test/local adapter, not a fallback.
- Historical imports and deleted modules are cleaned from tests and docs touched by this change.
- Code size/residue changes are reviewed against the AI-era programming principle: no misleading half-deleted paths.
