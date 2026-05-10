# Audit current Cortex/Sandbox/LogicalFS/Blob layering

## Problem

Before moving code, map the current active path and name the actual dependency/call flow. The audit must clarify whether the user's proposed ordering is semantically correct or whether the wording mixes call-flow and storage-substrate views.

## Success Criteria

- Active runtime entry points and module dependencies are identified with file/function pointers.
- The canonical layering is stated plainly.
- Any misleading current module placement is listed as concrete cleanup work.
