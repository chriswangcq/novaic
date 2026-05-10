# P034: Rewrite Final LogicalFS Architecture Docs

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P019/children/P024/children/P034
Body: problems/P000/children/P019/children/P024/children/P034/README.md
Ticket(s): T034

## Problem
Canonical docs still say registry uses `BlobCortexStore`, object-key docs still present `CortexLogicalFileAuthority`, and several docs imply Blob/Cortex owns live workspace files. This misleads future agents and humans.

## Success Criteria
- Canonical architecture docs describe final roles:
- Cortex owns semantic scope/workspace concepts.
- LogicalFS owns realtime `/ro` and `/rw`.
- Blob stores cheap bytes/objects below LogicalFS and artifacts/display/download payloads.
- sandboxd executes processes and receives mounted LogicalFS views.
- Stale canonical references to `CortexLogicalFileAuthority`, `BlobCortexStore`, and `blob_store.py` are removed or explicitly marked historical.
- Historical roadmap docs remain historical if edited minimally, but do not read as current canonical guidance.

## Subproblems
- none

## Results
- R032

## Latest Check
C032

## Bodies
- Problem: problems/P000/children/P019/children/P024/children/P034/README.md
- Ticket T034: problems/P000/children/P019/children/P024/children/P034/tickets/T034.md
- Result R032: problems/P000/children/P019/children/P024/children/P034/results/R032.md
- Check C032: problems/P000/children/P019/children/P024/children/P034/checks/C032.md

## Follow-ups
- none
