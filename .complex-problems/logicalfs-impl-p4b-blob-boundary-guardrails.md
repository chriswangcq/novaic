# Add Blob live RO/RW bypass guardrails

## Problem

The repository needs tests or scripts that fail if new direct Blob/object calls
become live `RO` / `RW` file authorities outside the allowed boundary.

## Success Criteria

- Guardrails allow Blob payload/display/audio/attachment byte use.
- Guardrails allow transitional persistence adapter internals only in explicitly
  named files.
- Guardrails fail obvious direct `/v1/objects` or `BlobCortexStore` usage from
  Workspace/API/runtime/sandbox code.
- Guardrails are part of targeted tests or CI scripts.
