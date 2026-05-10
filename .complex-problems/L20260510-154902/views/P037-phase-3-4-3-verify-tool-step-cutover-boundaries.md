# P037: Phase 3.4.3: Verify tool step cutover boundaries

Status: done
Parent: P026
Root: P000
Package: problems/P000/children/P004/children/P026/children/P037
Body: problems/P000/children/P004/children/P026/children/P037/README.md
Ticket(s): T033

## Problem
After tool step event wiring, audit remaining legacy step writes and classify them before P026 closes.

## Success Criteria
- Focused step event tests pass.
- Full Cortex suite passes.
- Static scans document remaining `steps/*.json`, `steps/_index.jsonl`, and `payloads/*.json` writes.
- Any unresolved direct-only tool result bypass becomes a follow-up.

## Subproblems
- none

## Results
- R030

## Latest Check
C032

## Bodies
- Problem: problems/P000/children/P004/children/P026/children/P037/README.md
- Ticket T033: problems/P000/children/P004/children/P026/children/P037/tickets/T033.md
- Result R030: problems/P000/children/P004/children/P026/children/P037/results/R030.md
- Check C032: problems/P000/children/P004/children/P026/children/P037/checks/C032.md

## Follow-ups
- none
