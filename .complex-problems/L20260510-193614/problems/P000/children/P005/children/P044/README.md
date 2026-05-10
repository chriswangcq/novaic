# Phase 4D Payload Manifest Verification And Cleanup

## Problem

After manifest write/read semantics are wired, Phase 4 needs a verification gate proving Cortex payload semantics are no longer inferred only from BlobRefs. Old tests/docs that imply Blob owns semantics must be cleaned or classified as historical.

## Success Criteria

- Static searches prove payload semantic state is represented through manifest APIs on live write/read paths.
- Targeted payload/step/operational-store tests pass.
- Full Cortex tests and `py_compile` pass.
- Current docs explain Blob as raw byte storage and Cortex as manifest/status authority.
- Any remaining old payload/Blob wording is removed, updated, or explicitly classified as historical.
