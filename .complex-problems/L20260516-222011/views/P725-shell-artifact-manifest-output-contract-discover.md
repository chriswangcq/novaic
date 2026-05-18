# P725: Shell artifact manifest output contract discovery

Status: done
Parent: P722
Root: P000
Source Ticket: T715 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P725
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P725/README.md
Ticket(s): T716

## Problem
Discover the active shell/tool output contract for screenshot/artifact-producing CLI commands, especially `devicectl hd screenshot`, and verify whether shell stdout is constrained to terminal text plus artifact manifests instead of raw media bytes.

## Success Criteria
- Active shell output wrapping code for screenshot/artifact commands is identified with file pointers.
- Tests or docs proving raw media bytes/base64 are excluded from shell stdout are identified.
- Any active shell command path still printing raw screenshot/base64 bytes is listed as a remediation candidate.
- The result distinguishes current active shell behavior from historical archived outputs.

## Subproblems
- none

## Results
- R708

## Latest Check
C752

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P725/README.md
- Ticket T716: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P725/tickets/T716.md
- Result R708: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P725/results/R708.md
- Check C752: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P725/checks/C752.md

## Follow-ups
- none
