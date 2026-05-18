# Packaged Blob Binary Contract Recheck

## Summary

Success. R786 fixed the packaged startup script contract and R787 closed the remaining resource/generated storage binary boundary. Together they satisfy P806.

## Evidence

- R786 updates both packaged startup script copies to prefer `novaic-storage-a`, fallback only to historical `novaic-blob-service`, and emit explicit diagnostics when no binary exists.
- R786 verifies both scripts with `bash -n` and verifies the script copies are byte-identical.
- R787 inspects Tauri packaging config and proves `resources/backends` is the packaged source.
- R787 adds `novaic-storage-a` to `src-tauri/resources/backends` and verifies it matches the generated asset binary byte-for-byte.

## Criteria Map

- Active packaged startup scripts start the actual committed blob/storage binary name or clearly fail with diagnostic: satisfied by R786.
- Source resource and generated backend asset copies no longer disagree about intended blob/storage binary contract: satisfied by R786 script equality plus R787 binary synchronization.
- Targeted scans show only intentional binary references: satisfied by R786/R787 scan evidence.
- `bash -n` passes for modified packaged scripts: satisfied by R786 and repeated in R787.

## Execution Map

- Script contract patch landed first.
- Strict check found a remaining resource binary boundary gap.
- Follow-up synchronized `novaic-storage-a` into source resources.

## Stress Test

- The first result was intentionally rejected because a diagnostic-only script fix still left physical resource drift. The follow-up closed that exact drift.

## Residual Risk

- Dev source script references to `novaic-blob-service` are intentionally left for P807 because they are not packaged binary contract issues.
- Other resource backend binaries remain ignored build artifacts; P806 only covers the blob/storage mismatch found in P804.

## Result IDs

- R786
- R787
