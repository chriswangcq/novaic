# P063: Prepare Entangled Production Backup And Writer Freeze

Status: done
Parent: P042
Root: P000
Source Ticket: T061 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P042/children/P063
Body: problems/P000/children/P024/children/P027/children/P042/children/P063/README.md
Ticket(s): T062

## Problem
Before final migration, production Entangled's active SQLite files and runtime launch facts must be backed up, and upstream writers must be stopped or frozen so the final SQLite export has a stable source. This belongs under `P042` because production cutover must not import from a changing SQLite database.

## Success Criteria
- Active `/opt/novaic/data/entangled.db*` files are copied to a rollback archive with permissions and checksums recorded.
- Current production Entangled launch facts are recorded without raw secrets.
- A production service-token file is prepared so the restarted process can avoid raw token args.
- Upstream writer processes/services that can mutate Entangled are identified and stopped/frozen for the cutover window.
- Health or process evidence confirms the freeze state is understood before migration starts.
- A rollback note describes how to restore the backed-up SQLite runtime if later cutover steps fail.

## Subproblems
- none

## Results
- R059

## Latest Check
C061

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P042/children/P063/README.md
- Ticket T062: problems/P000/children/P024/children/P027/children/P042/children/P063/tickets/T062.md
- Result R059: problems/P000/children/P024/children/P027/children/P042/children/P063/results/R059.md
- Check C061: problems/P000/children/P024/children/P027/children/P042/children/P063/checks/C061.md

## Follow-ups
- none
