# Prepare Entangled Production Backup And Writer Freeze

## Problem

Before final migration, production Entangled's active SQLite files and runtime launch facts must be backed up, and upstream writers must be stopped or frozen so the final SQLite export has a stable source. This belongs under `P042` because production cutover must not import from a changing SQLite database.

## Success Criteria

- Active `/opt/novaic/data/entangled.db*` files are copied to a rollback archive with permissions and checksums recorded.
- Current production Entangled launch facts are recorded without raw secrets.
- A production service-token file is prepared so the restarted process can avoid raw token args.
- Upstream writer processes/services that can mutate Entangled are identified and stopped/frozen for the cutover window.
- Health or process evidence confirms the freeze state is understood before migration starts.
- A rollback note describes how to restore the backed-up SQLite runtime if later cutover steps fail.
