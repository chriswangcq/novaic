# P784: LogicalFS Sandbox VMuse Service Cleanup

Status: done
Parent: P750
Root: P000
Source Ticket: T774 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/README.md
Ticket(s): T781

## Problem
Clean business-agnostic infrastructure surfaces that still describe stale LogicalFS/Sandbox/VMuse boundaries or expose unused helper paths.

## Success Criteria
- LogicalFS public docs/metadata emphasize live `/ro` and `/rw` file authority and avoid stale snapshot/view/patch-first phrasing.
- Unused Sandbox filesystem helper surface is deleted or relocated if confirmed inactive, including exports/tests that keep it alive artificially.
- Source VMuse stale FastMCP direct-media entry path is removed or replaced with the current Blob/tool-output/display contract.
- Service-level focused tests pass for touched LogicalFS, Sandbox, and VMuse packages.

## Subproblems
- P791: LogicalFS Public Contract Cleanup
- P792: Sandbox Unused Filesystem Helper Cleanup
- P793: VMuse FastMCP Direct Media Entry Cleanup

## Results
- R782

## Latest Check
C829

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/README.md
- Ticket T781: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/tickets/T781.md
- Result R782: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/results/R782.md
- Check C829: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/checks/C829.md

## Follow-ups
- none
