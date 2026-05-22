# P062: Run Entangled Postgres WebSocket Sync Smoke

Status: done
Parent: P052
Root: P000
Source Ticket: T056 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P062
Body: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P062/README.md
Ticket(s): T059

## Problem
After a Postgres-mode staging runtime and smoke client exist, the actual WebSocket sync behavior must be proven and reported. Run the smoke against the staging `/v1/sync` endpoint, verify schema/full/head behavior, write/delta propagation, reconnect safety, persisted sync-version monotonicity, and stream ordering with `entangled_rowid`. This belongs under `P052` because it closes the high-risk runtime sync path before production cutover.

## Success Criteria
- The smoke connects to the Postgres-mode staging `/v1/sync` endpoint and records endpoint, entity names, frame types, and counts.
- Schema/full/head sync behavior is verified for representative form/list/stream entities or the closest available protocol frames are documented.
- A write is performed or observed and a delta/push path is verified without decreasing or resetting persisted sync versions.
- A controlled disconnect/reconnect or restart/reconnect check proves persisted versions remain safe.
- Stream ordering checks show no duplicate or skipped rows where `entangled_rowid` participates.
- The redacted report contains no tokens, cookies, DSNs, passwords, or payload secrets.
- The staging process is stopped after validation or its continued lifetime is explicitly justified.

## Subproblems
- none

## Results
- R055

## Latest Check
C057

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P062/README.md
- Ticket T059: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P062/tickets/T059.md
- Result R055: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P062/results/R055.md
- Check C057: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P062/checks/C057.md

## Follow-ups
- none
