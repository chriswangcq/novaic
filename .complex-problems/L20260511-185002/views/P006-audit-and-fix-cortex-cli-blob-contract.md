# P006: Audit and fix cortex CLI Blob contract

Status: done
Parent: P003
Root: P000
Package: problems/P000/children/P003/children/P006
Body: problems/P000/children/P003/children/P006/README.md
Ticket(s): T005

## Problem
`cortex payload` shell capability commands inspect Cortex payload refs. They must remain bounded text-inspection tools and must not become unbounded binary or Blob-sized stdout channels.

## Success Criteria
- `cortex payload read` has explicit bounded read modes and size limits.
- `cortex payload search` returns bounded match contexts.
- `cortex payload summarize` and `cortex payload qa` return model-produced text summaries/answers, not raw payload bytes.
- Any unbounded or artifact-like stdout behavior is fixed and verified.
- Evidence references concrete code paths and test results.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P003/children/P006/README.md
- Ticket T005: problems/P000/children/P003/children/P006/tickets/T005.md
- Result R003: problems/P000/children/P003/children/P006/results/R003.md
- Check C003: problems/P000/children/P003/children/P006/checks/C003.md

## Follow-ups
- none
