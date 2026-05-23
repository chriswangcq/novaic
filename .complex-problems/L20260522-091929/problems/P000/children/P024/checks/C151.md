# Remaining Service Cutovers Check

## Summary

`R135` proves the Gateway, Cortex, Entangled, and Queue cutover work is substantially complete, but `P024` is not yet successful because the final central SQLite classification table still has stale active top-level rows for Gateway and Cortex. The original problem explicitly requires the final classification note to identify remaining SQLite files as rollback-only snapshots or justified non-service data.

## Blocking Gaps

- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` still classifies `/opt/novaic/data/gateway.db` as active auth/ops state in its top table row, even though Gateway has been cut over and the live file is absent.
- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` still classifies `/opt/novaic/data/cortex/operational.sqlite3` as active-projection-cache in its top table row, even though Cortex has been cut over and the live file is absent.
- The final classification audit artifact reports `needs_followup=true` with stale rows for Gateway and Cortex, so the final classification criterion is not satisfied.

## Result IDs

- R135
