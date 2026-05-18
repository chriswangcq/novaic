# Cortex Archive Diagnostics Source Map

## Problem

Before changing the archive path, identify the exact current functions, request schemas, payload fields, tests, and event writers involved in `CORTEX_SCOPE_END` from wake finalize through Cortex archive/context-event persistence.

## Success Criteria

- Lists the runtime wake-finalize payload builder, task handler, bridge/client, Cortex API request model, archive function, and context-event writer involved.
- Identifies which finalize diagnostics are currently preserved, dropped, inferred, or synthesized.
- Identifies existing tests that should be extended or replaced.
- Produces clear implementation targets for boundary propagation and archive persistence children.

## Why Under P368

P368 spans multiple packages. A source map prevents patching only the first visible function while leaving another old archive path active.
