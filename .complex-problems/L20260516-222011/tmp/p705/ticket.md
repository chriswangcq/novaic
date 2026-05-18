# Ticket: Cortex semantic state/context boundary classification

## Problem Definition
Classify Cortex as a semantic state/context/scope service with concrete code, launch, storage, and dependency evidence. Verify it consumes or orchestrates LogicalFS, Blob, Sandboxd, Queue, and Runtime without claiming ownership of their responsibilities.

## Proposed Solution
Inspect Cortex entrypoints, server/app launch scripts, context stack, workspace/state adapters, sandbox adapters, and docs. Produce a boundary map with active evidence and classify any misleading ownership claims as patched-safe or residual follow-up.

## Acceptance Criteria
- Cortex entrypoints and launch surfaces are identified with file/line evidence.
- Cortex long-term state responsibilities are separated from LogicalFS/Blob file-object storage and Sandboxd process execution.
- Cortex dependencies on Queue/Runtime are classified without collapsing worker/session ownership into Cortex.
- Any safe active stale claim discovered in Cortex-facing files is patched or recorded as a follow-up if too broad.

## Verification Plan
Use `rg`, `find`, and targeted file reads over `novaic-cortex`, docs, app startup scripts, and generated resource wrappers. Run focused syntax/tests/lints for any touched Cortex or boundary files. If no code changes are required, verify by scans and py_compile only.
