# P684: Extracted service entrypoint classification

Status: done
Parent: P673
Root: P000
Source Ticket: T677 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/README.md
Ticket(s): T689

## Problem
Classify independent service entrypoints for Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, and related service wrappers. Verify whether the repository reflects the intended architecture where foundational file/sandbox services are separate services rather than hidden Cortex internals.

## Success Criteria
- Service entrypoint files and start commands/configs are identified with evidence.
- Each service's current role and dependency boundary is summarized.
- Stale or duplicate service entrypoints that can be safely removed or clarified are handled, otherwise recorded.
- Relevant import/syntax/static checks are run if code changes occur.

## Subproblems
- P695: Extracted service entrypoint and launch evidence discovery
- P696: Foundational file and sandbox service boundary classification
- P697: Semantic, app, and device service boundary classification
- P698: Extracted service entrypoint residue cleanup and verification

## Results
- R814

## Latest Check
C863

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/README.md
- Ticket T689: problems/P000/children/P007/children/P668/children/P673/children/P684/tickets/T689.md
- Result R814: problems/P000/children/P007/children/P668/children/P673/children/P684/results/R814.md
- Check C863: problems/P000/children/P007/children/P668/children/P673/children/P684/checks/C863.md

## Follow-ups
- none
