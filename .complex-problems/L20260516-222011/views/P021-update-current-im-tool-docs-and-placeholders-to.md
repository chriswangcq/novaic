# P021: Update current IM tool docs and placeholders to shell contract

Status: done
Parent: P018
Root: P000
Source Ticket: none (none)
Source Check: C007
Package: problems/P000/children/P001/children/P009/children/P015/children/P018/children/P021
Body: problems/P000/children/P001/children/P009/children/P015/children/P018/children/P021/README.md
Ticket(s): T011

## Problem
Current-facing docs and UI placeholders still imply IM capabilities are direct LLM tools. Update them to the current shell-first contract: direct tools are minimal, while IM actions are performed through `agentctl im ...` inside shell.

## Success Criteria
- Current docs no longer describe `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, or `im_context` as active direct LLM tools.
- Docs describe IM actions through shell `agentctl im read/reply/send/history/search/context`.
- UI placeholder strings no longer advertise `im_read` as a direct tool example.
- Historical roadmap docs may remain if clearly historical and not current contract docs.
- Focused residue search confirms no current-facing stale IM direct-tool wording remains in the edited surfaces.

## Subproblems
- none

## Results
- R007

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P018/children/P021/README.md
- Ticket T011: problems/P000/children/P001/children/P009/children/P015/children/P018/children/P021/tickets/T011.md
- Result R007: problems/P000/children/P001/children/P009/children/P015/children/P018/children/P021/results/R007.md
- Check C008: problems/P000/children/P001/children/P009/children/P015/children/P018/children/P021/checks/C008.md

## Follow-ups
- none
