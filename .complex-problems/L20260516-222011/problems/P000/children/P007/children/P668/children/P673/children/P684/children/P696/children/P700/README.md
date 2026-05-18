# LogicalFS boundary map

## Problem

Classify LogicalFS as the realtime logical RO/RW file authority above Blob. Verify active module/service surfaces, backing storage dependencies, and boundaries against Cortex and Sandbox.

## Success Criteria

- LogicalFS entrypoint/module evidence is recorded with stable paths.
- LogicalFS role is summarized as live workspace/file authority, not cheap Blob storage and not Cortex semantic state.
- Cortex usages are classified as consumers/facades unless evidence proves ownership.
- Misleading LogicalFS boundary claims are patched or recorded.
