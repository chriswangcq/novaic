# Create LogicalFS substrate package

## Problem

LogicalFS needs a business-agnostic substrate that understands only snapshot/view/patch contracts, materialization, diffing, path sanitization, and view handles. This package must not know Cortex, agentctl, subagents, or process execution.

## Success Criteria

- `novaic-logicalfs` package exists with explicit DTOs for snapshot, file entries, writable layout, env overlay, view handle, and patch.
- Package can materialize a snapshot to local RO/RW roots and produce a patch from RW changes.
- Package has unit tests for materialization, deletion/change diffing, layout env, cwd validation, and path sanitization.
- Package imports no Cortex, sandbox core, sandbox sdk, agent runtime, agentctl, or product business modules.
