# P006: Wire Factory chat route streaming response and logging

Status: done
Parent: P001
Root: P000
Source Ticket: T001 (split)
Source Check: none
Package: problems/P000/children/P001/children/P006
Body: problems/P000/children/P001/children/P006/README.md
Ticket(s): T003

## Problem
The Factory route must honor `stream=true` by returning a streaming response from supported providers and must keep `stream=false` behavior unchanged. Unsupported provider streams should fail clearly.

## Success Criteria
- `/v1/chat/completions` returns streaming chunks when `stream=true` for OpenAI-compatible providers.
- Unsupported native provider streaming returns a clear error instead of silently falling back.
- Log records are completed or failed consistently for streaming calls.
- Existing non-streaming route tests continue to pass.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P001/children/P006/README.md
- Ticket T003: problems/P000/children/P001/children/P006/tickets/T003.md
- Result R001: problems/P000/children/P001/children/P006/results/R001.md
- Check C001: problems/P000/children/P001/children/P006/checks/C001.md

## Follow-ups
- none
