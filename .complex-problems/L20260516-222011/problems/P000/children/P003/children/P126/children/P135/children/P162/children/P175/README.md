# Runtime read_context caller inventory and guard coverage

## Problem

All remaining `read_context` or `context.read` call sites in runtime code/tests must be inventoried and tied to guard coverage, so future changes cannot confuse safe inspection with provider authority.

## Success Criteria

- `rg` inventory of runtime `read_context`, `context.read`, continuity, cross-wake, and historical-context terms is recorded.
- Each active production caller is classified.
- Static or behavioral guard tests for provider non-authority are identified and run.
- Any unclassified production caller is fixed or split.
