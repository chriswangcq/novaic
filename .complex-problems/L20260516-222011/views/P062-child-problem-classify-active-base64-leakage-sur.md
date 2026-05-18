# P062: Child Problem: classify active base64 leakage surfaces

Status: done
Parent: P053
Root: P000
Source Ticket: T053 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/children/P062
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/children/P062/README.md
Ticket(s): T054

## Problem
Before adding a broad guard, the active code paths and legitimate fixtures need classification. Otherwise the guard may either miss the real public-text leak paths or flag legitimate provider-native image payloads.

## Success Criteria
- Active source/test occurrences of `/9j/`, `data:image`, `base64`, display, shell, and image projection are scanned.
- Legitimate structured image payload uses are separated from forbidden public text/log/context leakage.
- The audit identifies exactly where a guard should live.

## Subproblems
- none

## Results
- R048

## Latest Check
C060

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/children/P062/README.md
- Ticket T054: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/children/P062/tickets/T054.md
- Result R048: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/children/P062/results/R048.md
- Check C060: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P053/children/P062/checks/C060.md

## Follow-ups
- none
