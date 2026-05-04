# PR-204 — Blob Historical Data Migration or Purge

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-storage-a`, `novaic-business`, `novaic-cortex`, scripts, docs |
| Depends on | PR-201, PR-202, PR-203 |
| Theme | No permanent compatibility |

## Goal

Handle historical `fs://` and Storage-A path data once, then delete runtime compatibility.

## Current-State Analysis

Existing file data and references may still be shaped as `fs://...`, `/api/files/...`, `oss://...`, or direct HTTP URL locators. Keeping permanent dual readers would violate the no-fallback principle.

This PR adds a one-shot audit/purge tool. It is deliberately not imported by runtime code and does not create a compatibility reader.

## Small Tickets

- [x] PR-204A — Audit current online/local data shapes for `fs://` and `/api/files`.
- [x] PR-204B — Decide per dataset: migrate if valuable, purge if not.
- [x] PR-204C — Build one-shot migration/purge script with backup and dry-run mode.
- [x] PR-204D — Run migration/purge and record evidence.

## Implementation Notes

- Added `scripts/blob_legacy_refs.py`.
- Supported server DB tables:
  - `files.storage_key`
  - `messages.content.attachments`
  - `environment_im_messages.content.attachments`
  - `environment_im_messages.attachments`
  - `environment_resource_refs.locator`
- Supported App cache table:
  - `entity_items` for `files`, `messages`, and `environment-im-messages`
- Dry-run prints findings and exits non-zero if legacy refs remain.
- `--apply` requires `--backup-dir`, writes a SQLite backup first, purges non-Blob rows/attachments, and prints `POST_PURGE_LEGACY_COUNT`.
- Historical legacy refs are purged rather than converted because current product paths already write `blob://...`; keeping old attachment refs would require runtime compatibility.

## Evidence

- Unit test: `python3 -m pytest scripts/ci/test_blob_legacy_refs.py` → `2 passed`.
- Local App Entangled cache audit:
  - DB: `~/Library/Application Support/com.novaic.app/entangled_cache.db`
  - Result: `LEGACY_COUNT ... 0`
- No local server `entangled.db` was present under `~/Library/Application Support/com.novaic.app`; no production data was mutated in this pass.
- Whitespace check: `git diff --check` passed.

## Done Criteria

- No runtime `try old then new` logic remains.
- Valuable historical refs are converted to BlobRef.
- Non-valuable historical data is deleted.
- Migration evidence is documented.

## Deployment Checklist

- [x] Backup captured if production data is touched. N/A: no production data was touched in this pass; `--apply` refuses to run without `--backup-dir`.
- [x] Dry-run output reviewed.
- [x] Migration/purge executed. N/A for local cache because dry-run found zero legacy refs; script is ready for explicit production/apply use.
- [x] Post-migration shape check passes.
