# P022 Blob Adapter Boundary Check

## Summary

Success for P022. The live Blob object adapter implementation moved below the LogicalFS package boundary, Cortex registry no longer constructs `BlobCortexStore`, and the old Cortex adapter source/test files were deleted. Stale docs and guardrail allowlists remain, but those are explicitly scoped to P024 cleanup.

## Evidence

- `novaic-logicalfs/logicalfs/blob_store.py` defines `BlobObjectStore`.
- `novaic-logicalfs/logicalfs/__init__.py` exports `BlobObjectStore`.
- `novaic-cortex/novaic_cortex/registry.py:16` imports `BlobObjectStore` from `logicalfs`.
- `novaic-cortex/novaic_cortex/registry.py:54-59` constructs `BlobObjectStore`, not `BlobCortexStore`.
- `novaic-cortex/novaic_cortex/blob_store.py` was deleted.
- `novaic-cortex/tests/test_blob_store.py` was deleted and replaced by `novaic-logicalfs/tests/test_blob_store.py`.
- Active-source scan found no `BlobCortexStore` or `novaic_cortex.blob_store` under `novaic-cortex/novaic_cortex` or `novaic-logicalfs/logicalfs`.

## Criteria Map

- LogicalFS owns Blob object persistence adapter: satisfied by `logicalfs.BlobObjectStore`.
- Live registry/workspace no longer imports or constructs `BlobCortexStore`: satisfied by active-source scan and registry pointer.
- Old Cortex wrapper removed or unreachable: satisfied by deleted source file and deleted Cortex test.
- Blob remains available for attachments/display/artifacts/downloads: satisfied because this ticket did not remove `blob_payload.py` or shell byte flows; targeted Cortex boundary tests still passed.
- Adapter tests prove behavior without Cortex imports: satisfied by `novaic-logicalfs/tests/test_blob_store.py` and `10 passed`.

## Execution Map

- Added LogicalFS Blob adapter and test.
- Updated Cortex registry construction.
- Deleted old Cortex adapter and old Cortex adapter test.
- Ran targeted LogicalFS and Cortex boundary tests.

## Stress Test

- Verified both direct active-source residue and behavior through Blob Service ASGI test app.
- Verified Cortex guardrail and sandbox wiring tests still pass after registry import changes.
- Checked that stale `BlobCortexStore` hits now live in docs/test-policy/roadmap, not active source.

## Residual Risk

- Guardrail policy still has transitional `BlobCortexStore` allowlist snippets; P024 must tighten them.
- Docs still mention the old adapter; P024 must rewrite those.
- `Workspace` still accepts the object adapter through the old store-shaped constructor; P023 must cut that boundary.

## Result IDs

- R021
