# P056: Child Problem: provider adapters receive image payloads through the right contract

Status: done
Parent: P051
Root: P000
Source Ticket: T043 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/README.md
Ticket(s): T046

## Problem
Even if runtime context assembly creates image blocks, provider adapters may still flatten or redact them incorrectly. The provider-facing contract must carry images in the format expected by the active LLM API while keeping logs/redaction safe.

## Success Criteria
- Provider adapters accept the runtime image representation without converting it to plain text.
- LLM Factory logs redact image bytes while preserving the fact that an image input was sent.
- Focused tests cover provider request redaction and image payload preservation.

## Subproblems
- P057: Add direct provider adapter image payload tests

## Results
- R040

## Latest Check
C054

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/README.md
- Ticket T046: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/tickets/T046.md
- Result R040: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/results/R040.md
- Check C050: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/checks/C050.md
- Check C054: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P051/children/P056/checks/C054.md

## Follow-ups
- P057: Add direct provider adapter image payload tests
