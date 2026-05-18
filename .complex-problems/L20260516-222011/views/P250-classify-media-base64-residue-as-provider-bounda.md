# P250: Classify media/base64 residue as provider-boundary-only or fix it

Status: done
Parent: P130
Root: P000
Source Ticket: T241 (split)
Source Check: none
Package: problems/P000/children/P003/children/P130/children/P250
Body: problems/P000/children/P003/children/P130/children/P250/README.md
Ticket(s): T244

## Problem
Search results may still show `data:image`, `/9j/`, or base64-like fixtures. Those occurrences must either be tests for provider/display boundaries or be fixed if they imply normal history leakage. This belongs under P130 because residue can confuse future maintainers and agents.

## Success Criteria
- Residue scan across runtime, Cortex, common, and LLM factory media paths is recorded.
- Any live code/comment that treats base64 as ordinary text history is corrected.
- Remaining base64/media fixtures are documented as test/provider-boundary-only.

## Subproblems
- P251: Runtime/context media residue classification
- P252: Cortex and shell CLI media residue classification
- P253: Provider and factory fixture media residue classification
- P254: Final repository cross-scan and residue closure

## Results
- R245

## Latest Check
C260

## Bodies
- Problem: problems/P000/children/P003/children/P130/children/P250/README.md
- Ticket T244: problems/P000/children/P003/children/P130/children/P250/tickets/T244.md
- Result R245: problems/P000/children/P003/children/P130/children/P250/results/R245.md
- Check C260: problems/P000/children/P003/children/P130/children/P250/checks/C260.md

## Follow-ups
- none
