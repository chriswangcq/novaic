# P074: Business dispatch adapter residue scan

Status: done
Parent: P071
Root: P000
Source Ticket: T064 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/README.md
Ticket(s): T066

## Problem
Business dispatch/subscriber code may still carry fallback compatibility or migration-era paths around IM aggregation, dispatch, ownership, or queue handoff.

## Success Criteria
- Focused scans cover `novaic-business` active code for legacy, fallback, compat, migration, TODO/FIXME, and old direct tool or dispatch wording.
- Hits are classified by active path status and risk.
- Safe tiny cleanup is applied directly if found.
- Focused business tests pass for touched files.

## Subproblems
- P076: Business dispatch active residue scan and safe cleanup

## Results
- R066

## Latest Check
C079

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/README.md
- Ticket T066: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/tickets/T066.md
- Result R066: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/results/R066.md
- Check C079: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P074/checks/C079.md

## Follow-ups
- none
