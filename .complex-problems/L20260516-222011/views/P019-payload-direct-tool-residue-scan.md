# P019: Payload direct tool residue scan

Status: done
Parent: P015
Root: P000
Source Ticket: T009 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P015/children/P019
Body: problems/P000/children/P001/children/P009/children/P015/children/P019/README.md
Ticket(s): T012

## Problem
Search for active direct LLM exposure or stale docs of `payload_read`, `payload_search`, `payload_summarize`, and `payload_qa` outside the intended `cortex payload ...` shell CLI and guard tests.

## Success Criteria
- Active code/tests/docs are searched with `.complex-problems` excluded.
- Valid references inside CLI implementation and absence-guard tests are identified.
- Stale or misleading references are fixed if found.
- Current direct LLM tool schemas remain free of payload tools.

## Subproblems
- P022: Remove tracked generated complex-problems dashboard residue

## Results
- R008

## Latest Check
C012

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P015/children/P019/README.md
- Ticket T012: problems/P000/children/P001/children/P009/children/P015/children/P019/tickets/T012.md
- Result R008: problems/P000/children/P001/children/P009/children/P015/children/P019/results/R008.md
- Check C010: problems/P000/children/P001/children/P009/children/P015/children/P019/checks/C010.md
- Check C012: problems/P000/children/P001/children/P009/children/P015/children/P019/checks/C012.md

## Follow-ups
- P022: Remove tracked generated complex-problems dashboard residue
