# P047: Phase 5C Current Docs And Comments Cleanup

Status: done
Parent: P006
Root: P000
Package: problems/P000/children/P006/children/P047
Body: problems/P000/children/P006/children/P047/README.md
Ticket(s): T055

## Problem
Even after code cleanup, stale comments and current docs can mislead future agents into treating in-memory locks, temp sandbox paths, BlobRefs, or file walks as authority. Current architecture documentation and live-code comments need to reflect the final state authority boundaries.

## Success Criteria
- Remove or rewrite current docs/comments that imply `/tmp/novaic-cortex-sandbox-*` backing paths are stable authority.
- Remove or rewrite current docs/comments that imply in-process locks, process-local state, or file walks are production authority.
- Keep historical docs only if their historical status is explicit from path/title/body.
- Update architecture guard docs with the forbidden-residue patterns.
- Static doc/code comment audit has no unclassified current residue.

## Subproblems
- P057: Phase 5C.1 Current Documentation And Comment Residue Audit
- P058: Phase 5C.2 Current Cortex Docs Update
- P059: Phase 5C.3 Live Source Comments And Docstrings Cleanup
- P060: Phase 5C.4 Documentation Residue Final Static Gate

## Results
- R057

## Latest Check
C061

## Bodies
- Problem: problems/P000/children/P006/children/P047/README.md
- Ticket T055: problems/P000/children/P006/children/P047/tickets/T055.md
- Result R057: problems/P000/children/P006/children/P047/results/R057.md
- Check C061: problems/P000/children/P006/children/P047/checks/C061.md

## Follow-ups
- none
