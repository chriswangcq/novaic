# P437: Runtime bridge endpoint inventory

Status: done
Parent: P436
Root: P000
Source Ticket: T425 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/README.md
Ticket(s): T426

## Problem
The runtime-to-Cortex bridge may still call context, payload, and tool-result endpoints through old helper names. Before changing behavior, create a precise inventory of all bridge callers and endpoint owners.

## Success Criteria
- Search artifacts list every runtime/Cortex caller of `/v1/context/read`, `/v1/context/append`, `/v1/context/batch`, `/v1/payload/*`, `/v1/tool-result/*`, `read_context`, `append_context`, `batch_context`, `prepare_for_llm`, and projection helpers.
- Each hit is classified as live agent loop, notification injection, debug/inspection, bounded payload inspection, test-only, or unresolved.
- No implementation change is made in this child except evidence files.
- Unresolved hits are carried into later child problems.

## Subproblems
- P441: Runtime bridge focused test fixture misses explicit session_generation

## Results
- R419

## Latest Check
C445

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/README.md
- Ticket T426: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/tickets/T426.md
- Result R419: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/results/R419.md
- Check C445: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/children/P436/children/P437/checks/C445.md

## Follow-ups
- none
