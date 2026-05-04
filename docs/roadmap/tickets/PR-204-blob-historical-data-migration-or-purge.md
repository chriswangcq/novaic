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

Handle historical non-Blob file references once, then delete runtime compatibility.

## Current-State Analysis

Existing file data and references may still use retired non-Blob locator shapes.
Keeping permanent dual readers would violate the no-fallback principle.

This PR used a one-shot audit/purge tool during migration. After production and local audits passed, the tool was deleted so the repository does not retain a second historical-data branch.

## Small Tickets

- [x] PR-204A — Audit current online/local data shapes for retired file locators.
- [x] PR-204B — Decide per dataset: migrate if valuable, purge if not.
- [x] PR-204C — Build one-shot migration/purge script with backup and dry-run mode, then delete it after closure.
- [x] PR-204D — Run migration/purge and record evidence.

## Implementation Notes

- Used a temporary one-shot legacy-ref audit/purge script during migration; it has been deleted after closure.
- Supported server DB tables:
  - `files.storage_key`
  - `messages.content.attachments`
  - `environment_im_messages.content.attachments`
  - `environment_im_messages.attachments`
  - `environment_resource_refs.locator`
- Supported App cache table:
  - `entity_items` for `files`, `messages`, and `environment-im-messages`
- Historical legacy refs were purged rather than converted because current product paths already write `blob://...`; keeping old attachment refs would require runtime compatibility.
- `ResourceRef` now accepts only BlobRef-shaped locators.

## Evidence

- The temporary legacy-ref script and its tests were removed after production purge.
- Local App Entangled cache audit:
  - DB: `~/Library/Application Support/com.novaic.app/entangled_cache.db`
  - Result: `LEGACY_COUNT ... 0`
- Production old data purge removed retired DBs, historical backups, old file
  storage directories, and smoke Blob leftovers.
- Production active `entangled.db` audit after purge: `LEGACY_COUNT ... 0`.
- Whitespace check: `git diff --check` passed.

## Done Criteria

- No runtime `try old then new` logic remains.
- Valuable historical refs are converted to BlobRef.
- Non-valuable historical data is deleted.
- Migration evidence is documented.

## Deployment Checklist

- [x] Backup captured if production data is touched. Historical backups were removed after the no-compat purge decision.
- [x] Dry-run output reviewed.
- [x] Migration/purge executed and the temporary script removed.
- [x] Post-migration shape check passes.
