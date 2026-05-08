# P000: Repair Agent Message Dispatch To Runtime

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Production accepted a user IM message but did not deliver it into the queue/session runtime, so the agent monitor did not react and no reply was produced. Prior diagnosis identified the immediate failure as Business subscriber `ReadTimeout` while posting `/api/queue/dispatch`, and the deeper failure as Queue Service SQLite/global FIFO lock contention plus saga claim 500s with `sqlite3.OperationalError: database is locked`.

Fix the production code path end to end: message dispatch must reliably enter the queue/session ledger, saga claiming must not 500 under normal worker polling, and a post-deploy smoke test must prove a new IM can produce queue/runtime activity.

## Success Criteria
- Code removes the known `sqlite3.OperationalError: database is locked` failure mode from saga claim / FSM event-store writes under normal worker polling.
- Business subscriber dispatch to Queue Service uses explicit production timeout and does not fail from the previous 5s default timeout.
- Queue dispatch / saga claim behavior has targeted tests.
- Production is deployed.
- Smoke test sends or injects a real user IM and verifies:
- Entangled message and notification are created.
- Notification dispatch succeeds or remains processable without failing.
- Queue session events include the new message.
- Saga/task/runtime pipeline shows activity instead of silent monitor inactivity.
- Remaining risks are recorded explicitly if full reply generation depends on external LLM/provider behavior.

## Subproblems
- P001: Code repair queue dispatch and saga claim
- P002: Targeted regression tests
- P003: Deploy and production smoke

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R003: problems/P000/results/R003.md
- Check C003: problems/P000/checks/C003.md

## Follow-ups
- none
