# Confirm Queue Freeze Window Approval

## Problem

Executing the final SQLite backup requires stopping production Queue writers and creates a brief Queue write freeze. The operator must explicitly approve that freeze window before execution.

## Success Criteria

- Operator approval is recorded in the ledger.
- Approval includes permission to stop Queue Service, workers, outbox workers, scheduler/health, and Queue-dependent ingress listed in the runbook.
- If approval is denied or deferred, the freeze/backup execution remains blocked and no production process is stopped.
