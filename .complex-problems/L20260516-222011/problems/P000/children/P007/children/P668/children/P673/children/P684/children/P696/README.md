# Foundational file and sandbox service boundary classification

## Problem

Classify Blob, LogicalFS, and Sandbox/Sandboxd as foundational infrastructure services. Verify their entrypoints, roles, and dependency boundaries, especially that Blob remains a cheap file server, LogicalFS owns realtime RO/RW logical file behavior, and Sandbox/Sandboxd owns execution/mount behavior without hidden Cortex ownership.

## Success Criteria

- Blob, LogicalFS, and Sandbox/Sandboxd each have role, entrypoint, and dependency-boundary evidence.
- Any Cortex-to-foundational-service calls are classified as service usage rather than ownership.
- Any stale code/docs implying Cortex owns foundational file/sandbox internals are patched or recorded.
- Touched files receive focused syntax/static checks.
