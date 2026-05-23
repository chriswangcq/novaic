# Purge Rollback-Only SQLite Artifacts

## Problem Definition

Production has already been migrated to Postgres, but rollback-only SQLite database files and sidecars remain under `/opt/novaic` as retained evidence. The user now explicitly wants all such SQLite artifacts deleted, accepting that rollback from SQLite snapshots will no longer be available.

## Proposed Solution

Inventory SQLite database files and sidecars under `/opt/novaic`, check for live file holders, delete all targeted SQLite files, write a deletion report with size/hash evidence, update the central SQLite classification note to say rollback SQLite artifacts were retired by this purge, and verify no targeted SQLite files remain. Preserve reports and notes, but remove database files and sidecars themselves.

## Acceptance Criteria

- Pre-delete inventory lists every targeted SQLite database file and sidecar under `/opt/novaic`.
- Deletion blocks if any targeted SQLite file has a live holder.
- Targeted SQLite database files and sidecars are deleted.
- Audit report records deleted paths, size, SHA256, and reason.
- Central SQLite classification note no longer says rollback SQLite database files are retained.
- Post-delete inventory shows no targeted SQLite database files or sidecars remain under `/opt/novaic`.
- Lightweight health/readiness checks for migrated services still pass where available.

## Verification Plan

Run remote inventory and lsof checks, perform deletion through a single auditable script, update classification text, copy sanitized reports locally, scan artifacts for credential patterns, verify no target files remain, and run lightweight health/readiness checks.

## Risks

- SQLite-file rollback will no longer be possible after deletion.
- Some non-production tooling may contain unrelated SQLite caches under `/opt/novaic`; the purge target is database files and sidecars under production/service/archive paths, with skipped items documented if any.

## Assumptions

- Postgres is the current source of truth for all service state.
- The user explicitly approved deleting rollback SQLite artifacts.
