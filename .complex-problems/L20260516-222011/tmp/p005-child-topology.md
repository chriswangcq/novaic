# LogicalFS Sandbox Blob Topology Map

## Problem

Map the current files, imports, and runtime call paths among Cortex, LogicalFS, sandbox service/core, and blob service. This child belongs under P005 because cleanup decisions require a precise layer map before removing any path.

## Success Criteria

- Lists relevant local repositories/modules with file references.
- Explains intended ownership of RO/RW real-time file semantics versus blob artifact storage.
- Identifies main CLI/service entrypoints and tests covering the layer.
- Records exact discovery commands.
