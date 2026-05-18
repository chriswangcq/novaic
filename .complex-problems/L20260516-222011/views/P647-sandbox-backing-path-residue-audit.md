# P647: Sandbox Backing Path Residue Audit

Status: done
Parent: P632
Root: P000
Source Ticket: T642 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P632/children/P647
Body: problems/P000/children/P005/children/P554/children/P632/children/P647/README.md
Ticket(s): T644

## Problem
Stable shell/filesystem contracts must not expose or depend on ephemeral `novaic-cortex-sandbox-*` backing paths. Remaining references need classification and cleanup if they define user/agent-facing behavior.

## Success Criteria
- Scans for `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW` where needed.
- Classifies hits as stable contract, defensive diagnostic, test fixture, historical artifact, or active ephemeral-path leak.
- Removes or creates follow-up for active ephemeral-path leak paths.

## Subproblems
- none

## Results
- R640

## Latest Check
C681

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/children/P647/README.md
- Ticket T644: problems/P000/children/P005/children/P554/children/P632/children/P647/tickets/T644.md
- Result R640: problems/P000/children/P005/children/P554/children/P632/children/P647/results/R640.md
- Check C681: problems/P000/children/P005/children/P554/children/P632/children/P647/checks/C681.md

## Follow-ups
- none
