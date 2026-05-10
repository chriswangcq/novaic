# P060: Source-of-truth language and artifact cleanup

Status: done
Parent: P006
Root: P000
Package: problems/P000/children/P006/children/P060
Body: problems/P000/children/P006/children/P060/README.md
Ticket(s): T060

## Problem
Remove stale docs/comments/test names that describe `context.jsonl`, `steps`, or `summary.md` as the authoritative LLM source. Materialized files may remain only as projection/debug artifacts.

## Success Criteria
- Static scans identify and classify source-of-truth wording.
- Misleading wording is deleted or rewritten.
- Remaining artifact reads are explicitly debug/projection/inspection, not active source semantics.

## Subproblems
- none

## Results
- R058

## Latest Check
C061

## Bodies
- Problem: problems/P000/children/P006/children/P060/README.md
- Ticket T060: problems/P000/children/P006/children/P060/tickets/T060.md
- Result R058: problems/P000/children/P006/children/P060/results/R058.md
- Check C061: problems/P000/children/P006/children/P060/checks/C061.md

## Follow-ups
- none
