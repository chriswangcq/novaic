# P799: VMuse remove deleted main imports

Status: done
Parent: P797
Root: P000
Source Ticket: none (none)
Source Check: C822
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P797/children/P799
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P797/children/P799/README.md
Ticket(s): T788

## Problem
After deleting `novaic_mcp_vmuse.main`, source `cli.py` and package comments still reference `.main`, so the console script can fail and the deleted FastMCP entry is still advertised.

## Success Criteria
- Source `cli.py` no longer imports `.main`, `mcp`, or `SKILLS_DIR` from deleted `main.py`.
- Source package comments no longer describe `main.py`/FastMCP as an available entry point.
- A focused scan finds no `.main import` references in source VMuse.

## Subproblems
- none

## Results
- R777

## Latest Check
C823

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P797/children/P799/README.md
- Ticket T788: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P797/children/P799/tickets/T788.md
- Result R777: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P797/children/P799/results/R777.md
- Check C823: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P797/children/P799/checks/C823.md

## Follow-ups
- none
