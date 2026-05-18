# P259: Cortex projection regression coverage

Status: done
Parent: P132
Root: P000
Source Ticket: T254 (split)
Source Check: none
Package: problems/P000/children/P003/children/P132/children/P259
Body: problems/P000/children/P003/children/P132/children/P259/README.md
Ticket(s): T255

## Problem
Cortex step result projection is one side of the cross-layer contract. It must prove that `tool-output.v1` artifact manifests, display perception projection, history projection, current non-display projection, and payload pointer behavior are covered by focused tests.

## Success Criteria
- Focused Cortex projection tests pass.
- Tests prove history/current non-display projections do not include raw image/base64 data.
- Tests prove explicit display perception is the only Cortex projection mode allowed to include image media.
- Tests prove shell screenshot artifact manifests remain text/manifest-only until explicit display is requested.

## Subproblems
- P263: Cortex projection coverage inventory
- P264: Cortex projection missing regression implementation
- P265: Cortex projection focused verification

## Results
- R255

## Latest Check
C270

## Bodies
- Problem: problems/P000/children/P003/children/P132/children/P259/README.md
- Ticket T255: problems/P000/children/P003/children/P132/children/P259/tickets/T255.md
- Result R255: problems/P000/children/P003/children/P132/children/P259/results/R255.md
- Check C270: problems/P000/children/P003/children/P132/children/P259/checks/C270.md

## Follow-ups
- none
