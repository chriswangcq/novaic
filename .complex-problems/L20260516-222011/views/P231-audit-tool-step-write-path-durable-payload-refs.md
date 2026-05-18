# P231: Audit tool step write path durable payload refs

Status: done
Parent: P229
Root: P000
Source Ticket: T222 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P231
Body: problems/P000/children/P003/children/P129/children/P229/children/P231/README.md
Ticket(s): T223

## Problem
The tool/step write path must store heavy tool output as durable payload records and preserve `step_ref`/`payload_ref` metadata instead of embedding raw large results in normal step records.

This belongs under `P229` because write-time storage is the first boundary that determines whether later context assembly can stay pointer-based.

## Success Criteria
- Active tool handler to Cortex write path is mapped with file/function pointers.
- Step write implementation evidence shows `payload_ref`/`step_ref` are required, generated, or preserved for heavy tool output.
- Tests or focused probes verify durable payload refs are emitted for representative shell/display-like output.

## Subproblems
- P235: Audit Cortex workspace step payload persistence
- P236: Audit runtime tool handler durable payload handoff

## Results
- R223

## Latest Check
C237

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P231/README.md
- Ticket T223: problems/P000/children/P003/children/P129/children/P229/children/P231/tickets/T223.md
- Result R223: problems/P000/children/P003/children/P129/children/P229/children/P231/results/R223.md
- Check C237: problems/P000/children/P003/children/P129/children/P229/children/P231/checks/C237.md

## Follow-ups
- none
