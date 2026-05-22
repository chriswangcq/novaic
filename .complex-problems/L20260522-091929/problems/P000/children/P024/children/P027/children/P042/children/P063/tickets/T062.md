# Prepare Production Entangled Backup And Writer Freeze

## Problem Definition

Before importing production SQLite into Postgres, Entangled's active SQLite files must be backed up and upstream writers must be frozen so the final migration source is stable. The current production process also uses a raw service-token argument, so this step should prepare a file-based service token for the later Postgres restart without printing the token.

## Proposed Solution

Create a timestamped cutover archive under `/opt/novaic/residue-archive`, copy `/opt/novaic/data/entangled.db*` into it with checksums, capture sanitized runtime launch facts, extract the current service token only into a root-only secret file for later restart, identify writer processes that call Entangled (Business API/subscriber and any other local processes with Entangled URLs), stop or freeze those writers in a reversible way, and record a rollback/freeze report. Leave production Entangled itself on SQLite until the next migration/restart steps.

## Acceptance Criteria

- Active SQLite files are copied to a timestamped rollback archive.
- Checksums, sizes, and archive paths are recorded.
- Current production Entangled runtime facts are captured without raw secrets.
- `/opt/novaic/postgres/secrets/entangled_production_service_token` or equivalent exists with mode `600 root:root`.
- Upstream writer processes are identified and either stopped/frozen or explicitly marked safe/non-writer.
- The report names exactly which PIDs/services were stopped and how to restart them.
- Production Entangled remains SQLite-mode after this step.

## Verification Plan

Use sanitized process inspection, `lsof`, `sha256sum`, file stat checks, and health/runtime checks. Verify no raw token is printed, that backup files exist and match size/checksum expectations, that writer PIDs are no longer running after freeze, and that Entangled still reports health/ready on SQLite.

## Risks

- Stopping Business/subscriber writers may temporarily interrupt user-facing flows.
- Extracting a token from current process args is sensitive; write only to a root-only file and never echo it.
- If unexpected writers exist, this ticket should record them rather than proceeding to migration blindly.

## Assumptions

- Current production process args still contain the service token needed for file-based restart.
- The rollback archive from preflight can be reused or a new cutover-specific archive can be created.
- Later children own final migration, Entangled restart, smokes, and SQLite active-path cleanup.
