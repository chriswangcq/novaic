# P128: Agent runtime context client and history expansion audit

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P128
Body: problems/P000/children/P003/children/P128/README.md
Ticket(s): T216

## Problem
Agent runtime prepares LLM calls by reading Cortex step/context data and expanding `step_ref` results. This layer can accidentally defeat Cortex payload externalization by loading formatted results into history incorrectly or by mishandling current versus historical display calls.

## Success Criteria
- Runtime context preparation and step result client code paths are mapped with concrete file/function pointers.
- The runtime distinguishes current-round display/media projection from historical manifest-only replay.
- Runtime does not expand shell/payload/blob bytes beyond bounded terminal text and durable references.
- Active skill stack/system-message insertion is checked so it does not suppress or reorder current-round media projection.
- Targeted runtime tests prove no historical image/base64 injection and correct current-round image availability.

## Subproblems
- P225: Map runtime step result expansion path
- P226: Verify runtime current versus historical media boundary
- P227: Verify active-stack ordering does not suppress current display media

## Results
- R217

## Latest Check
C231

## Bodies
- Problem: problems/P000/children/P003/children/P128/README.md
- Ticket T216: problems/P000/children/P003/children/P128/tickets/T216.md
- Result R217: problems/P000/children/P003/children/P128/results/R217.md
- Check C231: problems/P000/children/P003/children/P128/checks/C231.md

## Follow-ups
- none
