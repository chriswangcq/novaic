# Classify SQLite Owners and Quarantine Stale Residue

## Problem Definition

The `api` host still has several SQLite files under `/opt/novaic/data` and `/opt/novaic/llm-factory/data`. Some are active state owners, some are projections/caches, and some appear to be stale residue. Before deleting or archiving anything, each file needs an evidence-backed ownership/disposition decision so the system no longer carries misleading empty databases.

Special attention is required for `business.db` and `device.db`: `business.db` is zero bytes with no active code references found so far, while `device.db` has empty local tables and startup code that may recreate it even though current durable device state appears to live in Entangled.

## Proposed Solution

Run an evidence-first inventory on `api`:

1. Enumerate SQLite files under `/opt/novaic/data` and `/opt/novaic/llm-factory/data`, capturing path, size, mtime, table list, and row counts.
2. Map each file to runtime owners using service startup paths, process/service configuration, open file handles where available, and code references from the local repository.
3. Classify each file as `active-state-owner`, `active-projection-cache`, `migrate-candidate`, `defer-high-risk`, `archive-residue`, or `delete-residue`.
4. Produce a durable inventory note on the `api` host and in the ledger result.
5. For files proven stale and safe, make a timestamped backup/archive first, then remove or rename the misleading live-looking residue so future agents do not treat it as current state.
6. For startup paths that intentionally recreate local empty databases, document that behavior and defer code changes to the appropriate migration/refactor problem rather than deleting files in a loop.

## Acceptance Criteria

- Every SQLite file under `/opt/novaic/data` and `/opt/novaic/llm-factory/data` has a recorded classification and evidence.
- Evidence includes size, mtime, tables, row counts, runtime owner, startup path, and code references or lack of code references.
- `business.db` receives a disposition decision and is archived/deleted or explicitly documented as non-current residue.
- `device.db` receives a disposition decision that accounts for the current `main_device.py` startup behavior and the actual durable device state owner.
- Any production file removal/rename is preceded by a timestamped archive under an obvious backup/residue location.
- Existing services remain healthy after any cleanup.

## Verification Plan

Run inventory commands on `api`, inspect database schemas/row counts with `sqlite3`, search the repo with `rg`, check service configuration/startup code, optionally check open file handles with `lsof` or `/proc`, then perform only the cleanup actions supported by evidence. After cleanup, verify target files no longer appear as misleading active DBs, archives exist, and `docker`, `novaic`, `nginx`, `novaic-llm-factory`, and relevant health endpoints still pass.

## Risks

- A zero-row or zero-byte SQLite file may still be recreated by startup code, so deleting it alone may not close the residue.
- `queue.db` is large and semantically complex; classifying it is safe, but migrating or deleting it is out of scope for this ticket.
- `device.db` may be a latent startup/code-path issue rather than purely a file cleanup issue.
- Removing a file without checking runtime ownership could break a service after restart.

## Assumptions

- The source tree in `/Users/wangchaoqun/new-build-novaic` corresponds closely enough to the deployed `api` service code to use for code-reference evidence.
- The current goal is cleanup of proven residue and documentation of non-current paths, not broad service migrations.
- Active SQLite state owners should remain in place until their own migration tickets are executed.
