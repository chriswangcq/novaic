# Audit runtime tool handler durable payload handoff

## Problem

Runtime tool handlers and the bridge to Cortex must pass heavy shell/display-like output as durable payload metadata/projections rather than embedding raw output in normal message history.

This belongs under `P231` because even correct workspace persistence fails if runtime handlers bypass it or send raw data as the public tool result.

## Success Criteria

- Runtime tool handler/bridge code paths for shell and display-like outputs are mapped with file/function pointers.
- Evidence shows heavy raw output is separated from public compact projection and carried as durable payload input where applicable.
- Focused runtime tests pass for shell/display projection and no raw base64/large stdout in normal tool messages.
