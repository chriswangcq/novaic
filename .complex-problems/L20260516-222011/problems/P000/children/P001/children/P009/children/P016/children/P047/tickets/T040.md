# Ticket: scan ephemeral Cortex backing path residue

## Problem Definition

Agents should use stable `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW` views rather than copied `/tmp/novaic-cortex-sandbox-*` backing paths. Scan for stale active guidance or code that leaks/reuses backing paths.

## Proposed Solution

- Search for `novaic-cortex-sandbox`, `/tmp/novaic-cortex`, `/cortex/ro`, `$RO`, and path-rewrite guard code.
- Fix active guidance that recommends backing paths.
- Classify historical examples/tests if any remain.

## Acceptance Criteria

- No active prompt/doc/tool instruction recommends backing path reuse.
- Shell guard and docs prefer stable paths.
- Focused scan/classification recorded.

## Verification Plan

- Focused `rg` scan.
- Run tests only if code changes.

## Risk

Historical incident docs may legitimately quote old backing paths; classify instead of deleting if useful.
