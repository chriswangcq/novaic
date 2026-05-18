# P060: Child Problem: Cortex shell step projection preserves terminal semantics

Status: done
Parent: P052
Root: P000
Source Ticket: T049 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P060
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P060/README.md
Ticket(s): T051

## Problem
Even if runtime shell output is bounded, Cortex step/context projection can accidentally rehydrate durable payloads or historical shell outputs into large text. The Cortex projection layer must keep shell observations terminal-shaped and pointer-oriented.

## Success Criteria
- Cortex projection does not re-inline full durable shell payloads into LLM history.
- Historical shell steps are represented as bounded terminal text or pointers.
- Focused tests or scans cover the shell step projection path.

## Subproblems
- none

## Results
- R045

## Latest Check
C057

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P060/README.md
- Ticket T051: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P060/tickets/T051.md
- Result R045: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P060/results/R045.md
- Check C057: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P052/children/P060/checks/C057.md

## Follow-ups
- none
