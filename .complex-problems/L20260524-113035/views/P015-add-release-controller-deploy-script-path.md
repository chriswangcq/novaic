# P015: Add release-controller deploy script path

Status: done
Parent: P003
Root: P000
Source Ticket: T009 (split)
Source Check: none
Package: problems/P000/children/P003/children/P015
Body: problems/P000/children/P003/children/P015/README.md
Ticket(s): T012

## Problem
Add image-based deploy support for the release-controller so deployment can pull/run an immutable controller image without rebuilding on the production host.

## Success Criteria
- `deploy` has a clear image-based release-controller command.
- The command rejects mutable image refs for non-local deployment.
- The command preserves existing `services-image` and `factory-image` behavior.
- Shell syntax validation passes.
- Local dry validation or help output documents the new command.

## Subproblems
- none

## Results
- R010

## Latest Check
C011

## Bodies
- Problem: problems/P000/children/P003/children/P015/README.md
- Ticket T012: problems/P000/children/P003/children/P015/tickets/T012.md
- Result R010: problems/P000/children/P003/children/P015/results/R010.md
- Check C011: problems/P000/children/P003/children/P015/checks/C011.md

## Follow-ups
- none
