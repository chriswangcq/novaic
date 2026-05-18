# P083: Scan and clean Cortex shell CLI adapter residue

Status: done
Parent: P075
Root: P000
Source Ticket: T073 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/children/P083
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/children/P083/README.md
Ticket(s): T075

## Problem
Cortex shell capability code owns `agentctl`, `devicectl`, payload access, and media/artifact shell contracts. It must not keep stale direct-tool, base64-as-text, or compatibility code paths after the new shell/display/blob contract.

## Success Criteria
- Active Cortex shell CLI code matches current terminal-text plus artifact-manifest contract.
- Direct-tool leftovers are removed or classified as guard/blocked vocabulary.
- Focused Cortex shell/tool projection tests pass.

## Subproblems
- none

## Results
- R068

## Latest Check
C081

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/children/P083/README.md
- Ticket T075: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/children/P083/tickets/T075.md
- Result R068: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/children/P083/results/R068.md
- Check C081: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/children/P083/checks/C081.md

## Follow-ups
- none
