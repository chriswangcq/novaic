# P237: Audit runtime shell handoff uses compact projection plus durable payload

Status: done
Parent: P236
Root: P000
Source Ticket: T225 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P237
Body: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P237/README.md
Ticket(s): T226

## Problem
The runtime shell path must expose terminal-like bounded text to the LLM while preserving raw command output as durable payload/artifact data where needed. It must not pass huge stdout/base64 as ordinary tool message text.

This belongs under `P236` because shell is the primary interface tool and the concrete regression source for oversized tool context.

## Success Criteria
- Runtime shell handler/projection code is mapped with file/function pointers.
- Evidence shows public shell result text is bounded/terminal-like and raw output is separated as durable payload or artifact metadata.
- Focused shell projection/runtime tests pass.

## Subproblems
- none

## Results
- R220

## Latest Check
C234

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P237/README.md
- Ticket T226: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P237/tickets/T226.md
- Result R220: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P237/results/R220.md
- Check C234: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/children/P237/checks/C234.md

## Follow-ups
- none
