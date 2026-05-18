# P365: Follow-Up: Remove Startup Rebuild Generation Default

Status: done
Parent: P364
Root: P000
Source Ticket: none (none)
Source Check: C366
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/children/P365
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/children/P365/README.md
Ticket(s): T353

## Problem
`queue_service/session_rebuild.py` still reconstructs active session state with:

```python
generation=int(context.get("session_generation") or 1)
```

This silently turns missing identity into a valid generation. The recovery/finalize identity model requires missing or invalid generation to be rejected or skipped, not defaulted.

## Success Criteria
- No production code under session rebuild defaults missing `session_generation` to `1`.
- Startup rebuild records active session only when the saga context carries positive explicit generation.
- Missing/invalid generation contexts are skipped without fabricating active session state.
- Existing session rebuild boundary/residue tests still pass.

## Subproblems
- none

## Results
- R346

## Latest Check
C367

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/children/P365/README.md
- Ticket T353: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/children/P365/tickets/T353.md
- Result R346: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/children/P365/results/R346.md
- Check C367: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/children/P351/children/P364/children/P365/checks/C367.md

## Follow-ups
- none
