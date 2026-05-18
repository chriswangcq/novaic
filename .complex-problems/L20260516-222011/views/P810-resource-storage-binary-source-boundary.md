# P810: Resource Storage Binary Source Boundary

Status: done
Parent: P806
Root: P000
Source Ticket: none (none)
Source Check: C833
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/children/P810
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/children/P810/README.md
Ticket(s): T798

## Problem
The packaged startup script now expects `novaic-storage-a`, and generated packaged assets contain that binary, but `novaic-app/src-tauri/resources/backends` does not. Decide and implement the correct source-of-truth boundary so source resources and generated assets no longer accidentally diverge.

## Success Criteria
- Inspect Tauri packaging/resource generation to determine whether `src-tauri/resources/backends` or `src-tauri/gen/apple/assets/backends` is the source of truth for committed backend binaries.
- If resources are the source of truth, add/synchronize `novaic-storage-a` into `src-tauri/resources/backends` and verify generated/resource copies agree as expected.
- If generated assets are intentionally the binary source of truth, add an explicit narrow marker/check that documents this boundary and prevents the resource directory absence from being mistaken for drift.
- Targeted scans and `ls`/`git ls-files` evidence show no accidental `novaic-storage-a`/`novaic-blob-service` mismatch remains.

## Subproblems
- none

## Results
- R787

## Latest Check
C834

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/children/P810/README.md
- Ticket T798: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/children/P810/tickets/T798.md
- Result R787: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/children/P810/results/R787.md
- Check C834: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P806/children/P810/checks/C834.md

## Follow-ups
- none
