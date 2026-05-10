# P028: Phase 3.6: Demote or delete legacy source writes and verify write cutover

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P028
Body: problems/P000/children/P004/children/P028/README.md
Ticket(s): T039

## Problem
After write paths emit events, any legacy source-of-truth writes must be deleted or explicitly demoted to projection/debug output. The codebase must not retain a parallel authoritative legacy write path.

## Success Criteria
- Direct legacy writes to `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `summary.md`, and lifecycle `meta.json` are either removed from active source-of-truth paths or labeled and routed as projections.
- Tests prove event log is the authoritative write artifact for all Phase 3 write paths.
- Static scans document any remaining legacy file writes and why they are projection/debug-only.
- Full Cortex tests pass.

## Subproblems
- P042: Phase 3.6.1: Mark legacy context/step/lifecycle file writes as projections
- P043: Phase 3.6.2: Remove runtime direct structural scope lifecycle bypass
- P044: Phase 3.6.3: Add write-path event authority tests
- P045: Phase 3.6.4: Static audit remaining legacy writes

## Results
- R049

## Latest Check
C052

## Bodies
- Problem: problems/P000/children/P004/children/P028/README.md
- Ticket T039: problems/P000/children/P004/children/P028/tickets/T039.md
- Result R049: problems/P000/children/P004/children/P028/results/R049.md
- Check C052: problems/P000/children/P004/children/P028/checks/C052.md

## Follow-ups
- none
