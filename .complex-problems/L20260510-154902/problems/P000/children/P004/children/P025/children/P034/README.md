# Phase 3.3.3: Verify context append/batch cutover boundaries

## Problem

After append/batch event wiring, audit that there is no hidden direct-only context write path for these endpoints and that remaining legacy `context.jsonl` writes are explicitly transitional.

## Success Criteria

- Focused append/batch event tests pass.
- Full Cortex suite passes.
- Static scans document remaining `context.jsonl` write sites and classify them.
- Any unresolved bypass becomes a follow-up before P025 closes.
