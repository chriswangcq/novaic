# Scope End Boundary Contract Propagation

## Problem

The runtime `CORTEX_SCOPE_END` path must forward explicit finalize diagnostics through handler and bridge boundaries instead of dropping them before Cortex receives the request.

## Success Criteria

- `CORTEX_SCOPE_END` handler validates and forwards explicit finalize diagnostics where supplied.
- `CortexBridge.scope_end` and the Cortex API request contract accept explicit `session_generation`, `finalize_reason`, and remaining-stack diagnostics.
- Missing or non-positive generation is rejected for finalize diagnostic archive requests.
- Non-finalize or legacy-neutral callers remain explicit and deterministic without hidden active-generation inference.
- Focused runtime bridge/handler tests prove the propagated request payload.

## Why Under P368

This child owns transport and contract propagation only; it does not decide how Cortex persists archive metadata.
