# Blob Adapter Boundary Move Result

## Summary

Moved the Blob object-store adapter out of `novaic-cortex` and into `novaic-logicalfs`. Cortex registry now constructs `logicalfs.BlobObjectStore` instead of `BlobCortexStore`, and the old Cortex `blob_store.py` active source file and old Cortex test were deleted.

## Done

- Added `novaic-logicalfs/logicalfs/blob_store.py` with `BlobObjectStore`.
- Exported `BlobObjectStore` from `novaic-logicalfs/logicalfs/__init__.py`.
- Added `novaic-logicalfs/tests/test_blob_store.py` covering put/get/exists/list/list_recursive/move_prefix against the Blob Service ASGI app.
- Updated `novaic-cortex/novaic_cortex/registry.py`:
  - imports `BlobObjectStore` from `logicalfs`;
  - removes `CortexStore` import and `BlobCortexStore` construction;
  - caches per-user LogicalFS object adapters.
- Deleted `novaic-cortex/novaic_cortex/blob_store.py`.
- Deleted `novaic-cortex/tests/test_blob_store.py`.

## Verification

- `cd novaic-logicalfs && PYTHONPATH=.:../novaic-common:../novaic-blob-service python3 -m pytest -q`
  - Result: `10 passed in 0.28s`.
- `cd novaic-cortex && PYTHONPATH=.:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common python3 -m pytest -q tests/test_blob_boundary_guard.py tests/test_sandboxd_wiring.py tests/test_no_cortex_s3_residue.py`
  - Result: `8 passed in 0.31s`.
- Active-source residue scan:
  - `rg -n "BlobCortexStore|novaic_cortex\\.blob_store" novaic-cortex/novaic_cortex novaic-logicalfs/logicalfs || true`
  - Result: no active source hits.
- Registry evidence:
  - `novaic-cortex/novaic_cortex/registry.py:16`
  - `novaic-cortex/novaic_cortex/registry.py:47`
  - `novaic-cortex/novaic_cortex/registry.py:54-59`

## Known Gaps

- Cortex `Workspace` still accepts a direct store-shaped object and constructs the old Cortex-owned authority; P023 covers that cutover.
- Documentation and test guardrail policy still mention `BlobCortexStore` / old `blob_store.py`; P024 must clean and tighten those residues.
- `BlobObjectStore` still uses Blob Service `/v1/objects` internally, which is intended below LogicalFS but must be explicitly allowed only inside the LogicalFS boundary guardrail in P024.

## Artifacts

- `novaic-logicalfs/logicalfs/blob_store.py`
- `novaic-logicalfs/tests/test_blob_store.py`
- `novaic-cortex/novaic_cortex/registry.py`
- Deleted `novaic-cortex/novaic_cortex/blob_store.py`
- Deleted `novaic-cortex/tests/test_blob_store.py`
