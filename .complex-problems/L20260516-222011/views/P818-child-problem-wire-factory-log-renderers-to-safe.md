# P818: Child Problem: Wire factory log renderers to safe projection

Status: done
Parent: P812
Root: P000
Source Ticket: T805 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P818
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P818/README.md
Ticket(s): T808

## Problem
After the projection helper exists, `factory-logs.html` renderers must consistently use it for raw request/response tabs, message bubbles, tool-call arguments, and relevant tool/schema detail rendering.

## Success Criteria
- Raw request and response tabs no longer render unprojected `JSON.stringify` output.
- Message content and reasoning/tool argument displays use projected values.
- Useful metadata remains visible for debugging.
- The visual layout remains readable in the static page.

## Subproblems
- none

## Results
- R798

## Latest Check
C847

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P818/README.md
- Ticket T808: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P818/tickets/T808.md
- Result R798: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P818/results/R798.md
- Check C847: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P786/children/P812/children/P818/checks/C847.md

## Follow-ups
- none
