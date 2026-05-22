# P061: Build Entangled WebSocket Sync Smoke Client

Status: done
Parent: P052
Root: P000
Source Ticket: T056 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P061
Body: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P061/README.md
Ticket(s): T058

## Problem
The current WebSocket protocol shape must be exercised by a reproducible command or script rather than manual observation. Inspect the Entangled server/client protocol enough to build or adapt a small smoke client that connects to `/v1/sync`, authenticates without exposing secrets, records frame types/counts, and can drive the checks required by `P052`. This belongs under `P052` because production cutover needs repeatable WebSocket proof, not only REST or offline SQL checks.

## Success Criteria
- The smoke client or documented command connects to a configurable Entangled WebSocket endpoint with a token read from a file or environment variable.
- The client records schema/full/head or closest available protocol frames with entity names and counts.
- The client can trigger or observe a write/delta path for representative entities.
- The client can test controlled disconnect/reconnect behavior.
- The client records enough stream ordering evidence to detect duplicate or skipped rows involving `entangled_rowid`.
- Local tests, dry-run checks, or protocol-level validation cover redaction and frame parsing without requiring production secrets.

## Subproblems
- none

## Results
- R054

## Latest Check
C056

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P061/README.md
- Ticket T058: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P061/tickets/T058.md
- Result R054: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P061/results/R054.md
- Check C056: problems/P000/children/P024/children/P027/children/P040/children/P052/children/P061/checks/C056.md

## Follow-ups
- none
