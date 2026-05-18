# P588: Runtime display durable payload is BlobRef-only

Status: done
Parent: P586
Root: P000
Source Ticket: T576 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/README.md
Ticket(s): T577

## Problem
`novaic-agent-runtime/task_queue/handlers/tool_handlers.py` currently stores display image bytes in `durable_payload.llm_content._mcp_content[].data`. This child problem must change runtime display durable payload construction so persisted step payloads contain only text, metadata, and BlobRef media references.

## Success Criteria
- `_display_durable_payload` never copies image `data` into durable payload.
- Durable payload carries enough metadata for later perception: BlobRef, mime type, size, and a stable media reference item.
- Public display output remains terminal-style text/placeholder and never includes base64.
- Existing direct runtime display behavior remains valid for immediate tool execution.

## Subproblems
- P592: Runtime display durable media refs must not depend on inline bytes

## Results
- R570

## Latest Check
C608

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/README.md
- Ticket T577: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/tickets/T577.md
- Result R570: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/results/R570.md
- Check C606: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/checks/C606.md
- Check C608: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/checks/C608.md

## Follow-ups
- P592: Runtime display durable media refs must not depend on inline bytes
