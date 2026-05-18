# P423: Workspace step and payload normalization cleanup

Status: done
Parent: P417
Root: P000
Source Ticket: T407 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P423
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P423/README.md
Ticket(s): T410

## Problem
Workspace step writing and payload normalization are the bridge between shell/tool outputs and ContextEvents. They must enforce pointer-oriented payloads and avoid inline result compatibility.

## Success Criteria
- Inspect `workspace.py` step writing, payload writing, payload reading, and manifest code.
- Verify tool steps reject inline `result` and externalize or reference payloads explicitly.
- Remove stale compatibility branches if they allow large inline payloads or ambiguous payload refs.
- Add focused tests if behavior changes.
- Run workspace/payload/step projection tests.

## Subproblems
- none

## Results
- R403

## Latest Check
C429

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P423/README.md
- Ticket T410: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P423/tickets/T410.md
- Result R403: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P423/results/R403.md
- Check C429: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P417/children/P423/checks/C429.md

## Follow-ups
- none
