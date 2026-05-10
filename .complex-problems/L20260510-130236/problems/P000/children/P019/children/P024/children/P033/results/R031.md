# Result: LogicalFS Boundary Guardrails Tightened

## Summary

P033 removed transitional Cortex object-authority allowlists and made the guardrail scan include the LogicalFS Blob adapter as the only allowed object API path.

## Done

- Replaced `ALLOWED_TRANSITIONAL_OBJECT_AUTHORITY_FILES` with `ALLOWED_OBJECT_AUTHORITY_FILES`.
- Removed allowlist entries for:
  - `novaic_cortex/blob_store.py`
  - `novaic_cortex/registry.py`
  - `novaic_cortex/store.py`
  - `novaic_cortex/workspace_files.py`
- Added `novaic-logicalfs/logicalfs` to the guardrail scan roots.
- Added the LogicalFS Blob object adapter as the only allowed `/v1/objects` path.
- Kept `BlobCortexStore` only as a forbidden pattern, not as an allowed snippet.

## Evidence

- Guardrail tests passed:

```text
4 passed in 0.02s
```

- Transitional allowlist residue scan:

```text
rg -n "ALLOWED_TRANSITIONAL_OBJECT_AUTHORITY_FILES|workspace_files|BlobCortexStore|transitional object adapter|novaic_cortex/blob_store.py" tests/blob_boundary_policy.py tests/test_blob_boundary_guard.py
tests/blob_boundary_policy.py:55:    "BlobCortexStore",
```

The remaining `BlobCortexStore` hit is the forbidden pattern that prevents reintroducing that old name.

## Residuals

- Documentation still contains old names; P034 owns doc cleanup.
