# Phase 3.4.3: Verify tool step cutover boundaries

## Problem

After tool step event wiring, audit remaining legacy step writes and classify them before P026 closes.

## Success Criteria

- Focused step event tests pass.
- Full Cortex suite passes.
- Static scans document remaining `steps/*.json`, `steps/_index.jsonl`, and `payloads/*.json` writes.
- Any unresolved direct-only tool result bypass becomes a follow-up.
