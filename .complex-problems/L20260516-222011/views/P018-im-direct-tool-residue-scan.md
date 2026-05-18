# P018: IM direct tool residue scan

Status: done
Parent: P015
Root: P000
Source Ticket: T009 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P018
Body: problems/P000/children/P001/children/P009/children/P015/children/P018/README.md
Ticket(s): T010

## Problem
Search for active direct LLM exposure or stale documentation of `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, or `im_context` outside the intended `agentctl im ...` shell CLI and guard tests.

## Success Criteria
- Active code/tests/docs are searched with `.complex-problems` excluded.
- Valid references inside CLI implementation and absence-guard tests are identified.
- Stale or misleading references are fixed if found.
- Current direct LLM tool schemas remain free of IM tools.

## Subproblems
- P021: Update current IM tool docs and placeholders to shell contract

## Results
- R006

## Latest Check
C009

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P018/README.md
- Ticket T010: problems/P000/children/P001/children/P009/children/P015/children/P018/tickets/T010.md
- Result R006: problems/P000/children/P001/children/P009/children/P015/children/P018/results/R006.md
- Check C007: problems/P000/children/P001/children/P009/children/P015/children/P018/checks/C007.md
- Check C009: problems/P000/children/P001/children/P009/children/P015/children/P018/checks/C009.md

## Follow-ups
- P021: Update current IM tool docs and placeholders to shell contract
