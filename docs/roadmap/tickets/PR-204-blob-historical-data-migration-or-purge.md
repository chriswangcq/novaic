# PR-204 — Blob Historical Data Migration or Purge

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-storage-a`, `novaic-business`, `novaic-cortex`, scripts, docs |
| Depends on | PR-201, PR-202, PR-203 |
| Theme | No permanent compatibility |

## Goal

Handle historical `fs://` and Storage-A path data once, then delete runtime compatibility.

## Current-State Analysis

Existing file data and references may still be shaped as `fs://...` or `/api/files/...`. Keeping permanent dual readers would violate the no-fallback principle.

## Small Tickets

- [ ] PR-204A — Audit current online/local data shapes for `fs://` and `/api/files`.
- [ ] PR-204B — Decide per dataset: migrate if valuable, purge if not.
- [ ] PR-204C — Build one-shot migration/purge script with backup and dry-run mode.
- [ ] PR-204D — Run migration/purge and record evidence.

## Done Criteria

- No runtime `try old then new` logic remains.
- Valuable historical refs are converted to BlobRef.
- Non-valuable historical data is deleted.
- Migration evidence is documented.

## Deployment Checklist

- [ ] Backup captured if production data is touched.
- [ ] Dry-run output reviewed.
- [ ] Migration/purge executed.
- [ ] Post-migration shape check passes.

