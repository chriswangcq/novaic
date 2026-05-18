# Cortex Archive Diagnostics Persistence Source Map

## Problem

Map the exact Cortex persistence points for `/v1/scope/end` before changing archive diagnostic event shape.

## Success Criteria

- Identify the code that builds `WakeArchived` event payloads.
- Identify where semantic active-stack `remaining_stack` is computed.
- Identify the safest place and shape for explicit runtime diagnostics.
- Confirm which focused tests need to change or be added.
