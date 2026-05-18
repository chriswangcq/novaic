# Sandbox service residue discovery

## Problem

Scan Sandbox service/code for stale local fallback, compatibility, direct materialize/writeback, mount caching, or ownership wording that conflicts with the current Sandbox service consuming LogicalFS views and providing execution isolation. This belongs under P757 because Sandbox is the execution layer below shell/Cortex orchestration.

## Success Criteria

- Sandbox service/source files are discovered and scanned with bounded commands.
- Suspicious hits are classified as current execution isolation behavior, adapter boundary, stale residue, or unrelated vocabulary.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.
