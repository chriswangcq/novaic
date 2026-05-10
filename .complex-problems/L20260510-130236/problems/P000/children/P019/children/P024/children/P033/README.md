# Tighten LogicalFS Boundary Guardrails

## Problem

`tests/blob_boundary_policy.py` still has transitional allowlist entries for old Cortex authority files, `BlobCortexStore`, and `/v1/objects` usage that should now live only in LogicalFS/Blob infrastructure.

## Success Criteria

- Guardrail policy no longer allows `novaic_cortex/workspace_files.py` or `BlobCortexStore`.
- Guardrail policy permits `/v1/objects` only in the LogicalFS Blob object adapter and Blob service/docs where appropriate, not Cortex runtime.
- Guardrail tests pass and fail the old direct-Cortex live file patterns.
