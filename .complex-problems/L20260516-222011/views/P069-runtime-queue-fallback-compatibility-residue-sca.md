# P069: Runtime queue fallback compatibility residue scan

Status: done
Parent: P066
Root: P000
Source Ticket: T060 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P069
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P069/README.md
Ticket(s): T061

## Problem
Runtime and queue handling code may still contain stale fallback/compatibility branches around session dispatch, tool output projection, shell/display handling, or old queue paths.

## Success Criteria
- Focused scans cover `novaic-agent-runtime` active code for fallback, compat, legacy, migration, TODO/FIXME, pass, skip, and old direct-tool wording.
- Hits are classified as active risk, intentional guard, benign adapter, or stale residue.
- Safe tiny cleanup is applied directly if discovered.
- Touched runtime areas receive focused tests or explicit no-code-change verification.

## Subproblems
- none

## Results
- R056

## Latest Check
C068

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P069/README.md
- Ticket T061: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P069/tickets/T061.md
- Result R056: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P069/results/R056.md
- Check C068: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P069/checks/C068.md

## Follow-ups
- none
