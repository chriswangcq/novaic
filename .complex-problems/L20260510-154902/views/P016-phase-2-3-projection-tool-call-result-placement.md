# P016: Phase 2.3: Projection tool call/result placement

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P016
Body: problems/P000/children/P003/children/P016/README.md
Ticket(s): T017

## Problem
Implement projection of assistant tool call and tool step events into LLM-compatible message order. This belongs under Phase 2 because tool results must be represented from events before read-path cutover can stop consulting legacy step files.

## Success Criteria
- Projector handles `AssistantToolCallRecorded` and `ToolStepRecorded`.
- Tool result messages are attached by `call_id` and preserve event order.
- Tool observation preview/summary data is included without fetching payload bytes.
- Orphan tool results without assistant call are still represented in a deterministic, loud/debuggable way.
- Tests cover assistant call + result, multiple tools, orphan result, and payload_ref preservation.

## Subproblems
- none

## Results
- R015

## Latest Check
C016

## Bodies
- Problem: problems/P000/children/P003/children/P016/README.md
- Ticket T017: problems/P000/children/P003/children/P016/tickets/T017.md
- Result R015: problems/P000/children/P003/children/P016/results/R015.md
- Check C016: problems/P000/children/P003/children/P016/checks/C016.md

## Follow-ups
- none
