# P127: Step result projection contract audit

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127
Body: problems/P000/children/P003/children/P127/README.md
Ticket(s): T174

## Problem
Step result projection is the boundary where raw tool output becomes LLM-visible history/current context. It must enforce terminal-style shell text, manifest-only historical artifacts, current-round display behavior, and no accidental inline large payloads.

## Success Criteria
- `step_result_projection` behavior is audited for shell, display, payload, blob artifact, and generic tool outputs.
- Historical display/tool results are proven to be manifest-only and do not reintroduce base64/image bytes.
- Current-round display behavior is proven to be provider-usable without polluting future history.
- Any active projection branch that emits raw base64 or unbounded tool text into text context is fixed.
- Regression tests cover shell bounded text, display current projection, display historical projection, and payload manifest behavior.

## Subproblems
- P184: Shell projection bounded terminal text
- P185: Current display projection provider media
- P186: Historical display and artifact manifest projection
- P187: Step result projection stale branch cleanup

## Results
- R213

## Latest Check
C227

## Bodies
- Problem: problems/P000/children/P003/children/P127/README.md
- Ticket T174: problems/P000/children/P003/children/P127/tickets/T174.md
- Result R213: problems/P000/children/P003/children/P127/results/R213.md
- Check C227: problems/P000/children/P003/children/P127/checks/C227.md

## Follow-ups
- none
