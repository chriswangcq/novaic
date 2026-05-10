# Guardrail Allowlist Policy Result

## Summary

Created a test-side executable policy module for the Blob/LogicalFS boundary. It names allowed Blob byte paths, transitional object authority files, forbidden live `RO` / `RW` authority source locations, and synthetic allowed/forbidden snippets for the guardrail implementation and proof tickets.

## Done

- Added `novaic-cortex/tests/blob_boundary_policy.py`.
- Encoded allowed Blob byte files:
  - `novaic_cortex/blob_payload.py`
  - `novaic_cortex/shell_capabilities.py`
  - test prefixes for Blob byte fixtures.
- Encoded allowed transitional object authority files:
  - `novaic_cortex/blob_store.py`
  - `novaic_cortex/registry.py`
  - `novaic_cortex/store.py`
  - `novaic_cortex/workspace_files.py`
- Encoded forbidden live-file authority source locations:
  - `novaic_cortex/api.py`
  - `novaic_cortex/logical_fs.py`
  - `novaic_cortex/runtime.py`
  - `novaic_cortex/sandbox.py`
  - `novaic_cortex/workspace.py`
  - `novaic-sandbox-service/sandbox_service/`
- Added helper functions and synthetic positive/negative snippets for P011/P012.

## Verification

- Ran `python3 -m py_compile novaic-cortex/tests/blob_boundary_policy.py`.
- The policy directly reflects the P006 audit classifications.

## Known Gaps

- P011 still needs to implement the actual scanning test using this policy.
- P012 still needs to prove the scanner catches synthetic forbidden bypasses.

## Artifacts

- `novaic-cortex/tests/blob_boundary_policy.py`
- `.complex-problems/logicalfs-impl-p4b1-result.md`
