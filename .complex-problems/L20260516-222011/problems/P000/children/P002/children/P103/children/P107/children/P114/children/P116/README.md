# Runtime Stale Cortex Backing Path Rejection Guard

## Problem

Runtime shell command handling must reject or block direct use of copied `novaic-cortex-sandbox-*` backing paths so old tool output cannot be pasted into later shell turns and silently break.

## Success Criteria

- Locate the runtime shell command guard that detects stale Cortex backing paths.
- Verify the guard catches `/tmp/novaic-cortex-sandbox-*` or equivalent ephemeral backing paths.
- Run focused tests for stale-path rejection.
- Fix any missing guard coverage without adding compatibility fallback behavior.
