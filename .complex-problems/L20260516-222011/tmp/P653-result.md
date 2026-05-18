# Audit Live Code for Blob-as-Workspace Authority result

## Summary

Audited live code for Blob-as-workspace authority. No active path was found where Cortex/Sandbox directly uses Blob object APIs as live workspace semantics. One guardrail false positive was found and fixed: `step_result_projection.py` legitimately projects `blob://` as a media BlobRef for LLM/display perception, without fetching bytes or owning workspace semantics.

## Classification

- `novaic-logicalfs/logicalfs/authority.py`: valid live `/ro`/`/rw` authority over a generic object-store protocol.
- `novaic-logicalfs/logicalfs/blob_store.py`: valid Blob object adapter below LogicalFS; not a semantic workspace API.
- `novaic-cortex/novaic_cortex/registry.py`: valid wiring that builds a Workspace from LogicalFS authority plus Blob object adapter; registry cache is not the durable authority.
- `novaic-cortex/novaic_cortex/blob_payload.py`: valid large tool-payload externalization to BlobRef; Cortex keeps payload semantics/manifests.
- `novaic-cortex/novaic_cortex/shell_capabilities.py`: valid display/audio byte fetch by explicit artifact BlobRef.
- `novaic-cortex/novaic_cortex/step_result_projection.py`: valid BlobRef projection into `image_ref` for visual LLM perception; no Blob byte fetch and no Workspace authority.
- `novaic-sandbox-service`: no direct Blob/LogicalFS dependency in service runtime; existing guardrail covers this boundary.

## Changes Made

- Renamed test-side guardrail concepts from “blob byte” to “blob reference” where appropriate.
- Added `novaic_cortex/step_result_projection.py` as an allowed BlobRef projection boundary.
- Added an allowed snippet for LLM media BlobRef projection.

## Verification

- Live scan captured in `.complex-problems/L20260516-222011/tmp/P653-live-code-blob-scan.txt`.
- High-risk file list captured in `.complex-problems/L20260516-222011/tmp/P653-live-code-files.txt`.
- Boundary tests passed after guardrail fix:

```text
cd novaic-cortex && PYTHONPATH="$PWD:$PWD/../novaic-logicalfs:$PWD/../novaic-common:$PWD/../novaic-sandbox-sdk" python -m pytest tests/test_blob_boundary_guard.py tests/test_workspace_registry_dependencies.py -q
7 passed in 0.05s
```

## Residual Risk

Low. The only changed runtime-facing artifact is a test policy allowlist; production code was not changed. The allowlist now more accurately separates BlobRef projection from Blob byte/object authority.
