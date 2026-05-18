# Blob Service Boundary Map

## Classification

Blob Service is a foundational byte/object storage service. It owns stored bytes, object-tree primitives, tenant-isolated metadata, BlobRef creation/validation flows, direct Blob edge data-plane behavior, lifecycle limits, and backend storage selection (local or S3/OSS-compatible).

Blob Service does not own live Cortex/shell `/ro` or `/rw` workspace semantics, Cortex scope/step/summary meaning, tool observation meaning, prompt assembly, app/business product meaning, or Agent Monitor display copy.

## Entrypoint Evidence

- `novaic-blob-service/main_blob_service.py`: executable service entrypoint that imports `blob_service.main:main`.
- `novaic-blob-service/blob_service/main.py`: FastAPI app factory and argparse/uvicorn server entrypoint. Requires `--data-dir`, defaults to port `19995`, exposes `/api/health` and Blob routes.
- `novaic-blob-service/novaic-blob-service.spec`: packaged binary spec for the Blob Service entrypoint.

## Launch Evidence

- `scripts/start.sh`: launches Blob Service with `main_blob_service.py`, `--host`, `--port "$PORT_BLOB_SERVICE"`, and `--data-dir "$DATA_DIR"`; sets OSS/S3-compatible backend environment before launch.
- `scripts/build-all.sh`: includes `novaic-blob-service` in build output guidance.
- `novaic-blob-service/scripts/smoke_blob_service.sh`: standalone Blob Service smoke path.

## Dependency Boundary

- Blob is below LogicalFS. `docs/reference/blob-service.md` states that LogicalFS is the Cortex/shell realtime `RO`/`RW` authority above Blob and that Blob remains cheap byte/object infrastructure.
- Cortex can consume Blob for large payload bytes via `novaic-cortex/novaic_cortex/blob_payload.py` and can probe Blob health, but this is client usage, not ownership of Blob storage credentials or the live file view.
- LogicalFS can use Blob object APIs through adapters, but LogicalFS decides live workspace file semantics; Blob only stores bytes/object data.
- Gateway/App consume BlobRef and Blob edge paths for attachments/downloads; product meaning remains outside Blob.

## Residue Disposition

No safe production code or active docs patch was required in this ticket. Current high-signal docs already state the intended boundary: Blob is byte/object storage, LogicalFS is live workspace authority, Cortex owns semantic trace not Blob infrastructure. Historical roadmap docs may contain old migration context but are not active boundary definitions.

## Verification

- `python3 scripts/ci/lint_blob_workspace_boundary.py` passed.
- `python3 -m py_compile novaic-blob-service/main_blob_service.py novaic-blob-service/blob_service/main.py` passed.
