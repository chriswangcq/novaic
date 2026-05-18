# P067: Test skip TODO and fixture residue scan

Status: done
Parent: P017
Root: P000
Source Ticket: T059 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P067
Body: problems/P000/children/P001/children/P009/children/P017/children/P067/README.md
Ticket(s): T082

## Problem
Tests may contain stale skips, TODO/FIXME markers, compatibility fixtures, or old assertions that keep deprecated behavior acceptable.

## Success Criteria
- Focused scans cover active test directories for skip, xfail, TODO, FIXME, compat, fallback, and legacy markers.
- Hits are classified as intentional coverage, stale acceptance of old behavior, or harmless fixture text.
- Any tiny stale test residue is cleaned directly when safe.
- Risky or broad test rewrites are routed to explicit child/follow-up work.

## Subproblems
- P090: Runtime queue test residue scan
- P091: App test residue scan
- P092: Business Cortex Common test residue scan
- P093: MCP scripts and CI test residue scan

## Results
- R087

## Latest Check
C101

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P067/README.md
- Ticket T082: problems/P000/children/P001/children/P009/children/P017/children/P067/tickets/T082.md
- Result R087: problems/P000/children/P001/children/P009/children/P017/children/P067/results/R087.md
- Check C101: problems/P000/children/P001/children/P009/children/P017/children/P067/checks/C101.md

## Follow-ups
- none
