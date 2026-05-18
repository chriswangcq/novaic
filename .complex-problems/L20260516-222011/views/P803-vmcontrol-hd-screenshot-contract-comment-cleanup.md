# P803: VmControl HD screenshot contract comment cleanup

Status: done
Parent: P785
Root: P000
Source Ticket: T791 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P803
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P803/README.md
Ticket(s): T802

## Problem
VmControl HD tools Rust code contains stale screenshot-to-LLM comments that conflict with the current blob/display/tool-output contract.

## Success Criteria
- HD tools comments describe screenshot capture/storage/display through blob/display contract, not direct LLM base64/image injection.
- No stale screenshot-to-LLM wording remains in the relevant Rust route code.
- Rust formatting/check or targeted scan runs if available.

## Subproblems
- none

## Results
- R793

## Latest Check
C841

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P803/README.md
- Ticket T802: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P803/tickets/T802.md
- Result R793: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P803/results/R793.md
- Check C841: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P803/checks/C841.md

## Follow-ups
- none
