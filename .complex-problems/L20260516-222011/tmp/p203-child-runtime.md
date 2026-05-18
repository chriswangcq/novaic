# Runtime projection branch inventory

## Problem

Runtime expands context, selects step projections, processes multimodal messages, and formats shell tool results. We need a focused inventory of runtime projection branches.

## Success Criteria

- Inventory runtime code that selects step projections, handles `_projection`, strips/sanitizes image content, and bounds shell output.
- Classify suspicious runtime branches as active, compatibility, defensive, or stale.
- Identify cleanup candidates with file/line evidence.
- Do not edit code.
