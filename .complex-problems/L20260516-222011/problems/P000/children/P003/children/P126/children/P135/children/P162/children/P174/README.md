# Runtime wake continuity residue classification

## Problem

`runtime_handlers.py` and related wake/session logic can contain cross-wake, idempotency, or notification replay paths. These must be classified so they do not act as hidden LLM context fallbacks.

## Success Criteria

- `runtime_handlers.py` and relevant runtime wake/session call sites are mapped.
- Cross-wake, idempotency, and notification replay residues are classified as active-safe, stale, or risky.
- Tests such as no-wake-replay and child-scope guardrails are identified and run.
- Any active stale path that affects LLM provider input is fixed or split.
