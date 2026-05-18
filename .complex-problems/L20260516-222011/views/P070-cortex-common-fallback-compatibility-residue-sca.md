# P070: Cortex common fallback compatibility residue scan

Status: done
Parent: P066
Root: P000
Source Ticket: T060 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P070
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P070/README.md
Ticket(s): T062

## Problem
Cortex and common code may retain old compatibility branches around workspace paths, context projection, tool schemas, payload handling, or sandbox exposure.

## Success Criteria
- Focused scans cover `novaic-cortex` and `novaic-common` active code for fallback, compat, legacy, migration, TODO/FIXME, pass, skip, base64, and ephemeral path patterns.
- Hits are classified by active path status and risk.
- Safe tiny cleanup is applied directly if discovered.
- Touched Cortex/common areas receive focused tests or explicit no-code-change verification.

## Subproblems
- P072: Cortex common active PR history comment cleanup

## Results
- R058

## Latest Check
C070

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P070/README.md
- Ticket T062: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P070/tickets/T062.md
- Result R058: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P070/results/R058.md
- Check C070: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P070/checks/C070.md

## Follow-ups
- none
