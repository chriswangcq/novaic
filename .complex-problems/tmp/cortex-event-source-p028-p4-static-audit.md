# Phase 3.6.4: Static audit remaining legacy writes

## Problem

After projection naming, runtime helper removal, and event authority tests, remaining legacy filesystem writes must be statically audited before Phase 3 can close.

## Success Criteria

- Static scans list remaining writes to `context.jsonl`, `steps/*.json`, `steps/_index.jsonl`, `summary.md`, and lifecycle `meta.json`.
- Each remaining write is classified as projection/debug/support or becomes a follow-up.
- Full Cortex suite passes.
