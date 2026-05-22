# Archive Entangled SQLite Residue And Update Cutover Notes

## Problem Definition

Production Entangled has been migrated, restarted, and smoked successfully in Postgres mode, but `/opt/novaic/data/entangled.db*` still exists in the active data path and the central SQLite classification note still marks Entangled SQLite as an active state owner. Leaving those files and notes active creates rollback ambiguity and future operational confusion.

## Proposed Solution

Verify one last time that production Entangled is ready in Postgres mode and no process holds `/opt/novaic/data/entangled.db*`. Move any remaining active-path `entangled.db`, `entangled.db-wal`, and `entangled.db-shm` files into the existing timestamped cutover archive with clear rollback-only names. Write an Entangled rollback/cutover note with the archive path, Postgres runtime facts, smoke evidence, and restore steps. Update `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` so Entangled SQLite is marked archived/rollback-only and no longer active. Pull redacted notes/reports into local ledger artifacts.

## Acceptance Criteria

- Active-path `/opt/novaic/data/entangled.db*` files are absent after archival.
- Moved files are present in the cutover archive or recorded as already absent.
- No process holds any old Entangled SQLite file.
- Entangled still reports health/readiness HTTP 200 in Postgres mode after archival.
- Rollback note records archive path, Postgres runtime facts, smoke evidence, and restore steps.
- Central SQLite classification note marks Entangled SQLite as archived/rollback-only.
- Final local report records moved files, remaining files, and rationale.

## Verification Plan

Use remote `curl`, sanitized process inspection, `lsof`, `find/stat`, and shell moves under `/opt/novaic/data` and `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`. Avoid printing secret file contents. Fetch the updated note and final report into ledger artifacts.

## Risks

- Moving SQLite files before confirming no holders could break rollback or an unnoticed SQLite-mode process.
- Updating the central classification note incorrectly could hide queue or other SQLite files that are still active.
- Rollback steps must be explicit because the active path will no longer contain the original SQLite DB.

## Assumptions

- P065 and P066 have already proven production Entangled readiness and representative REST/WebSocket behavior on Postgres.
- The existing cutover archive is `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`.
- Business API/subscriber restart is handled by the next operational cutover step, not by this residue archival ticket.
