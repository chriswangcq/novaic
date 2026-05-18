# Cortex context event lifecycle cleanup

## Problem

Cortex context event lifecycle code may still contain generation defaults or compatibility branches that weaken the event-sourced context model.

## Success Criteria

- Inspect live context event API/store/assembly lifecycle hits from the Cortex inventory.
- Remove dangerous defaulting or implicit generation behavior, or replace it with explicit validation.
- Preserve legitimate event projection fields only with explicit classification.
- Add focused tests for any changed context event lifecycle boundary.
- Rerun focused Cortex context event tests.
