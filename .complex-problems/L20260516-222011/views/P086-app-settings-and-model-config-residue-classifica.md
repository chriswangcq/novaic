# P086: App settings and model config residue classification

Status: done
Parent: P085
Root: P000
Source Ticket: T077 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P086
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P086/README.md
Ticket(s): T078

## Problem
`novaic-app/src` contains non-monitor settings/model config hits such as provider compatibility names, local config legacy wording, and settings labels. These may be benign product vocabulary, but they need explicit classification and stale wording cleanup.

## Success Criteria
- Inspect settings/model config hits for fallback, compat, legacy, migration, and provider compatibility wording.
- Classify each hit as current product vocabulary, benign compatibility naming, stale comment, or active risk.
- Remove or rewrite stale comments/names when safe.
- Run focused tests or a no-code-change verification for the inspected settings/model files.

## Subproblems
- none

## Results
- R073

## Latest Check
C086

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P086/README.md
- Ticket T078: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P086/tickets/T078.md
- Result R073: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P086/results/R073.md
- Check C086: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/children/P086/checks/C086.md

## Follow-ups
- none
