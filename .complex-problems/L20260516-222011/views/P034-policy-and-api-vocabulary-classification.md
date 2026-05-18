# P034: Policy and API vocabulary classification

Status: done
Parent: P033
Root: P000
Source Ticket: T025 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P034
Body: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P034/README.md
Ticket(s): T026

## Problem
Policy allowlists and internal API endpoint names legitimately need to know about migrated direct-tool names, but those references should be mechanically isolated from active LLM-facing tool-surface vocabulary.

## Success Criteria
- Classify remaining policy/API direct-tool tokens.
- Keep necessary migration allowlists/endpoints, but name/comment them as migrated, legacy, or shell-capability backing APIs.
- Avoid ordinary docs/comments implying these names are active direct executors.
- Verify with focused grep and relevant tests/py_compile.

## Subproblems
- none

## Results
- R022

## Latest Check
C031

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P034/README.md
- Ticket T026: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P034/tickets/T026.md
- Result R022: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P034/results/R022.md
- Check C031: problems/P000/children/P001/children/P009/children/P015/children/P033/children/P034/checks/C031.md

## Follow-ups
- none
