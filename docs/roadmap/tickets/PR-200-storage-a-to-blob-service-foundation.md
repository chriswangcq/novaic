# PR-200 — Storage-A to Blob Service Foundation

| Field | Value |
| --- | --- |
| Status | `[planned]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-storage-a`, docs |
| Depends on | PR-199 |
| Theme | Storage-A de-businessing |

## Goal

Turn Storage-A from a product "File Service" into a Blob Service infrastructure boundary while keeping existing users untouched until each call path is deliberately migrated.

## Current-State Analysis

`novaic-storage-a` currently names its package, health contract, routes, and docs as `file_service` / Storage-A. It stores bytes on disk or OSS and has useful backend abstractions, but its API shape is still `/api/files/*` and it returns `fs://...`.

## Small Tickets

- [ ] PR-200A — Introduce Blob Service naming and internal contract without removing existing file facade.
- [ ] PR-200B — Add `/v1/blobs/*` put/get/stat/presign endpoints backed by the existing storage backend.
- [ ] PR-200C — Update health and tests to expose Blob contract version.
- [ ] PR-200D — Document `/api/files/*` as legacy facade only, not a new-code entrypoint.

## Done Criteria

- New Blob API exists and passes roundtrip tests.
- Existing `/api/files/*` remains only as explicitly marked compatibility facade until migrated.
- New code examples use `blob://...`, not `fs://...`.
- No product semantics are added to Blob Service.

## Deployment Checklist

- [ ] `novaic-storage-a` tests pass.
- [ ] Storage service deployed.
- [ ] Health check shows Blob Service contract.

