# Update Queue Postgres Cleanup Documentation

## Problem Definition

The production Queue service now runs from Postgres and its old SQLite active path has been archived, but `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` still describes `/opt/novaic/data/queue.db` as a deferred active state owner. That stale central note can mislead future operations, and the Queue rollback/retention policy is not yet documented in one durable place.

## Proposed Solution

Update the API host central SQLite classification note so Queue is classified as archived/rollback-only and non-current, with Postgres named as the runtime source of truth. Add a dedicated Queue cutover/rollback note in the cutover archive that records the archive directory, final backup checksum, production Postgres runtime facts, restore expectations, and a defined retention/retirement policy. Copy redacted note snapshots into local ledger artifacts and scan the local artifacts for credential patterns.

## Acceptance Criteria

- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` no longer classifies `/opt/novaic/data/queue.db` as an active state owner.
- The central classification note says Queue runtime source of truth is Postgres and SQLite is archived/rollback-only evidence.
- A Queue cutover/rollback note exists under `/opt/novaic/backups/queue-cutover/20260523T011125Z/`.
- The cutover/rollback note includes the final backup checksum, archived SQLite location, current runtime path, restore expectation, and retention/retirement policy.
- Redacted local artifact copies or summaries exist in `.complex-problems/L20260522-091929/artifacts/`.
- Local artifacts are scanned for DSNs, passwords, tokens, private keys, and raw Postgres secret paths.

## Verification Plan

Read the updated remote classification and rollback notes, verify required Queue phrases and paths are present, verify the old active classification phrase is absent from the Queue row, copy sanitized snapshots into local artifacts, and run a credential-pattern scan over the new artifacts.

## Risks

- The remote central note currently contains other services' credential-file paths; local evidence must be sanitized before committing.
- Documentation-only cleanup does not itself enforce runtime behavior, so it must cite the already completed Postgres health, ready, lsof, backup, and archive evidence.

## Assumptions

- Queue cutover evidence from `P123` through `P127` is valid and remains the source of operational facts.
- The archived SQLite file should be retained through the post-cutover stabilization window and only retired after a later explicit cleanup decision.
