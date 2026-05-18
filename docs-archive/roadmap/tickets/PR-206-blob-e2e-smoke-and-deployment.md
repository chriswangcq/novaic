# PR-206 — Blob End-to-End Smoke and Deployment Closure

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | all touched repos |
| Depends on | PR-199..PR-205 |
| Theme | Production closure |

## Goal

Close the Blob Service migration by proving the real product path works end to end.

## Current-State Analysis

The migration spans App, Gateway, Business, Runtime, Cortex, and Blob Service. Unit tests are necessary but not sufficient; a cross-service smoke is required.

## Small Tickets

- [x] PR-206A — App/Gateway upload path returns a BlobRef.
- [x] PR-206B — Runtime/Cortex payload path was covered by PR-202/PR-205 tests and deployed with Blob refs.
- [x] PR-206C — Agent Monitor path remains semantic; raw payload exposure is guarded by runtime/Cortex projection tests.
- [x] PR-206D — Local App Entangled cache audit shows no historical non-Blob refs.
- [x] PR-206E — Production config scan confirms old file/storage switches cannot revive.

## Done Criteria

- Full upload/read/preview/download path works.
- Runtime/Cortex large payload path works.
- Agent Monitor remains user-facing.
- Old branches are absent or guarded.
- Deploy evidence is recorded.

## Deployment Checklist

- [x] All service deploys completed.
- [x] Smoke evidence captured.
- [x] Parent repo submodule pointers pushed.
- [x] Oclow/backend architecture docs updated if needed.

## Implementation Notes

- Deployed all backend services via `./deploy services`; second deploy verified
  the production `start.sh` label now reports `Blob Service :19995`.
- Added deployment/runbook guard coverage for `deploy`, `scripts/start.sh`, and
  `novaic-app/scripts/start-backends.sh` so old file-service wording cannot
  re-enter active operational scripts.
- Updated the local dev start script to use Blob Service labels and logs.

## Verification

- `./deploy services` → all backend services restarted successfully.
- `./deploy status` → Entangled, Gateway, Business, Device, Queue, Blob Service,
  Cortex, workers, and relay active.
- Historical production Gateway upload/fetch smoke through loopback used the
  then-current temporary upload route and returned
  `blob://user-file/1777870667418-ffa72a140a2254f70ec778c1`.
  PR-216 later removed that route; active smokes should use multipart upload
  plus Gateway register/fetch.
- Production Blob Service health:
  `{"status":"ok","service":"blob-service","contract_version":"blob/v1"}`.
- Production active-code scan found no legacy file hot-path tokens in Gateway,
  Blob Service, Runtime, Common tool definitions, or Cortex.
- Server Entangled DB audit:
  `LEGACY_COUNT /opt/novaic/data/entangled.db 0`.
- Local App cache audit:
  `LEGACY_COUNT ~/Library/Application Support/com.novaic.app/entangled_cache.db 0`.
- Post-migration production purge removed retired compatibility DBs/backups and
  old file storage directories. Remaining active DBs are `entangled.db`,
  `gateway.db`, `queue.db`, and `device.db`.
- Active code now uses `blob_service`, `BLOB_SERVICE_URL`, and
  `main_blob_service.py`; the old package/entrypoint was physically removed.
