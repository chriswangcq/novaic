# Move Blob Object Persistence Below LogicalFS

## Problem

Live Cortex workspace construction can still reach `BlobCortexStore`, which makes Blob persistence feel like a Cortex-owned live file layer. Blob should remain a cheap byte/object server below LogicalFS, while LogicalFS owns realtime `RO` / `RW` file authority. This belongs under T019 because the final dependency boundary cannot be true while Cortex registry constructs a Blob-specific workspace store directly.

## Success Criteria

- Blob object persistence used for live `RO` / `RW` is represented as a LogicalFS-owned generic object store adapter or equivalent boundary.
- Live Cortex registry/workspace construction no longer imports or constructs `BlobCortexStore`.
- Any old Cortex Blob store wrapper is deleted, renamed out of the live path, or proven test-only with guardrails.
- Blob remains available for attachments/display/artifacts/downloads, but not as a direct Cortex live workspace API.
- Tests prove the adapter preserves object put/get/list/delete/move behavior without requiring Cortex imports.
