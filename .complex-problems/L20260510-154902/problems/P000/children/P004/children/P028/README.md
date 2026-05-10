# Phase 3.6: Demote or delete legacy source writes and verify write cutover

## Problem

After write paths emit events, any legacy source-of-truth writes must be deleted or explicitly demoted to projection/debug output. The codebase must not retain a parallel authoritative legacy write path.

## Success Criteria

- Direct legacy writes to `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `summary.md`, and lifecycle `meta.json` are either removed from active source-of-truth paths or labeled and routed as projections.
- Tests prove event log is the authoritative write artifact for all Phase 3 write paths.
- Static scans document any remaining legacy file writes and why they are projection/debug-only.
- Full Cortex tests pass.
