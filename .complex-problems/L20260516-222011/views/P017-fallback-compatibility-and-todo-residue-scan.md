# P017: Fallback compatibility and TODO residue scan

Status: done
Parent: P009
Root: P000
Source Ticket: T008 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017
Body: problems/P000/children/P001/children/P009/children/P017/README.md
Ticket(s): T059

## Problem
Search for stale fallback/compatibility branches, TODO/FIXME/pass/skip markers, and old migration comments that may violate the current no-backward-compatibility preference.

## Success Criteria
- Searches are bounded and exclude historical ledger noise where appropriate.
- Hits are triaged by risk and active path status.
- Tiny high-confidence cleanup is applied directly; larger issues are routed to specialized audit children.
- Result identifies whether any active old-compat code remains.

## Subproblems
- P066: Active code fallback and compatibility residue scan
- P067: Test skip TODO and fixture residue scan
- P068: Active docs migration and legacy residue scan

## Results
- R092

## Latest Check
C106

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/README.md
- Ticket T059: problems/P000/children/P001/children/P009/children/P017/tickets/T059.md
- Result R092: problems/P000/children/P001/children/P009/children/P017/results/R092.md
- Check C106: problems/P000/children/P001/children/P009/children/P017/checks/C106.md

## Follow-ups
- none
