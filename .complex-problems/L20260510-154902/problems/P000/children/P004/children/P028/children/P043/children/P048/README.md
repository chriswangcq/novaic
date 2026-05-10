# Verify runtime lifecycle bypass removal

## Problem

After method removal and test migration, the repository needs a strict audit proving there is no remaining direct runtime structural lifecycle bypass or test residue.

## Success Criteria

- Static scan finds no `def scope_create`, `def scope_end`, `.scope_create(`, or `.scope_end(` under active runtime/test code except the event-wired API functions themselves.
- No compatibility shim is introduced to keep old runtime lifecycle names alive.
- Full Cortex suite passes.
- Any remaining lifecycle call site is documented as API-level event-wired behavior, not runtime façade behavior.
