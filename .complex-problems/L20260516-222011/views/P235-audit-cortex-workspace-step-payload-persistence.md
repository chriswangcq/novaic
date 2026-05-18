# P235: Audit Cortex workspace step payload persistence

Status: done
Parent: P231
Root: P000
Source Ticket: T223 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P235
Body: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P235/README.md
Ticket(s): T224

## Problem
Cortex workspace persistence must create or preserve durable payload records for tool steps and expose compact `step_ref`/`payload_ref` metadata in step records instead of storing raw heavy results as normal context content.

This belongs under `P231` because workspace persistence is the canonical storage layer for tool step payload refs.

## Success Criteria
- Workspace payload write/read and step write functions are mapped with file/function pointers.
- Evidence shows active step write requires or receives payload/payload_ref and writes durable payload records for heavy content.
- Focused Cortex tests verify step write/index records include `payload_ref`/`step_ref` behavior.

## Subproblems
- none

## Results
- R219

## Latest Check
C233

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P235/README.md
- Ticket T224: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P235/tickets/T224.md
- Result R219: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P235/results/R219.md
- Check C233: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P235/checks/C233.md

## Follow-ups
- none
