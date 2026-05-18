# Materialized context owner classification

## Problem

Before renaming or deleting materialized context bridge helpers, classify each live use of `/v1/context/read`, `/v1/context/append`, and `/v1/context/batch` by its actual owner and purpose.

## Success Criteria

- Every live runtime/Cortex/test hit is classified as notification projection, assistant/system timeline projection, API test, debug/API compatibility, or dead residue.
- Evidence artifacts are saved.
- No code is changed in this child.
- The classification explicitly identifies which child should handle each non-clean owner.
