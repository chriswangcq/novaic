# P129: Payload API and pointer retrieval boundary audit

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129
Body: problems/P000/children/P003/children/P129/README.md
Ticket(s): T220

## Problem
Payload APIs are the intended way to inspect large outputs after context externalization. The boundary is only sound if full payload reads/search/summaries stay explicit, bounded, and pointer-addressed, while normal context assembly keeps only references and compact projections.

## Success Criteria
- Cortex payload read/search/summarize/qa APIs are mapped and verified against pointer-oriented expectations.
- Tool/step writes store large outputs through payload references rather than inline context entries.
- Payload reads are bounded or explicit, and no default LLM context path silently uses full payload reads.
- CLI/tool schema guidance points agents to explicit payload inspection instead of expecting inline history.
- Tests cover payload reference availability and bounded retrieval behavior.

## Subproblems
- P228: Audit explicit Cortex payload inspection APIs
- P229: Audit payload write and normal context assembly boundaries
- P230: Audit tool guidance and payload boundary tests

## Results
- R238

## Latest Check
C253

## Bodies
- Problem: problems/P000/children/P003/children/P129/README.md
- Ticket T220: problems/P000/children/P003/children/P129/tickets/T220.md
- Result R238: problems/P000/children/P003/children/P129/results/R238.md
- Check C253: problems/P000/children/P003/children/P129/checks/C253.md

## Follow-ups
- none
