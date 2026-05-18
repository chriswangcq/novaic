# Tool result step_ref and payload_ref map

## Problem

Tool results flow through runtime handlers into Cortex step and ContextEvent projections. The join keys `step_ref` and `payload_ref` must be stable and correctly distinguished, especially when payloads are externalized to blob references.

## Success Criteria

- Runtime tool result creation paths and Cortex projection handling of `step_ref`/`payload_ref` are mapped.
- The contract for stable `step_ref` versus actual/externalized `payload_ref` is documented.
- Tests prove externalized payloads keep stable step lookup refs while recording blob payload refs.
- Any ambiguous or duplicate key handling is fixed or split into a focused follow-up.
