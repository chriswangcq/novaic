# P151: Direct workspace write bypass scan

Status: done
Parent: P148
Root: P000
Source Ticket: T133 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P151
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P151/README.md
Ticket(s): T136

## Problem
Non-test code should not bypass `normalize_step`/`write_step_projection` with ad hoc step or context writes that can persist raw payload data. A repository-wide scan is needed to catch any remaining active bypass paths.

This belongs under `P148` because projection call-site correctness includes proving old direct write branches are gone or safely scoped.

## Success Criteria
- Repository scan maps all non-test `write_step`, `write_step_projection`, direct `steps/*.json`, and `_index.jsonl` write sites.
- Any non-test direct write is either removed, routed through the workspace boundary, or explicitly justified as non-tool-step behavior.
- Tests or source evidence cover the remaining active paths.

## Subproblems
- none

## Results
- R130

## Latest Check
C144

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P151/README.md
- Ticket T136: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P151/tickets/T136.md
- Result R130: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P151/results/R130.md
- Check C144: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P151/checks/C144.md

## Follow-ups
- none
