# Update Queue Postgres Source-Of-Truth Cleanup Notes

## Problem

The Queue SQLite active path has been archived after the production Postgres cutover, but the central SQLite classification and rollback notes still need to explicitly state that Queue runtime source of truth is Postgres and that the archived SQLite files are rollback-only evidence. The cleanup documentation must also define whether the archived SQLite artifact can be retired later or must be retained for a specific window.

## Success Criteria

- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` or the current central SQLite classification note marks Queue SQLite as archived/rollback-only and non-current, with Postgres named as the runtime source of truth.
- A rollback/cutover note records the Queue archive path, final backup checksum, Postgres runtime facts, restore expectation, and retention/retirement policy for the archived SQLite artifact.
- Local ledger artifacts include redacted copies or summaries of the updated notes.
- Updated notes are scanned for credential patterns before being recorded as evidence.
