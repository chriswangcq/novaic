# P758: Gateway Business Device test residue discovery

Status: done
Parent: P756
Root: P000
Source Ticket: none (none)
Source Check: C783
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/README.md
Ticket(s): T748

## Problem
P756 found useful Gateway, Business, and Device source-code residue candidates, but did not provide evidence that relevant tests were scanned. The remaining gap is to scan relevant test files for stale Gateway/Business/Device ownership, old media/control route, direct/fallback/compatibility, and screenshot/base64 residue, then classify any hits as intentional guard fixtures, current protocol tests, or remediation candidates.

## Success Criteria
- Relevant tests under `novaic-gateway`, `novaic-business`, and `novaic-device` are searched with bounded, reproducible commands.
- Test hits are classified separately from production code hits.
- Any stale or misleading active test fixture/comment is listed as a remediation candidate.
- No product code is modified in this discovery follow-up.

## Subproblems
- P759: Gateway test residue discovery
- P760: Business test residue discovery
- P761: Device test residue discovery

## Results
- R742

## Latest Check
C787

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/README.md
- Ticket T748: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/tickets/T748.md
- Result R742: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/results/R742.md
- Check C787: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/checks/C787.md

## Follow-ups
- none
