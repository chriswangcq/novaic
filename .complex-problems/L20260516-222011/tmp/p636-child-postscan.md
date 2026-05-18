# RW Scratch Cleanup Post-Scan Verification

## Problem

After layout and fixture changes, verify no Cortex code/test still advertises root `/rw/scratch` as the default/canonical scratch path.

## Success Criteria

- Runs post-change scans for `/rw/scratch`, `RW_SCRATCH`, and `/rw/subagents`.
- Classifies any remaining root `/rw/scratch` hits as lower-layer/out-of-scope or follow-up-worthy.
- Runs focused Cortex/LogicalFS tests needed to prove cleanup did not break current behavior.
