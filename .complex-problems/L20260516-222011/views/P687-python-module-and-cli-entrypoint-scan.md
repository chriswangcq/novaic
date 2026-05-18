# P687: Python module and CLI entrypoint scan

Status: done
Parent: P682
Root: P000
Source Ticket: T678 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P682/children/P687
Body: problems/P000/children/P007/children/P668/children/P673/children/P682/children/P687/README.md
Ticket(s): T680

## Problem
Find Python service/worker entrypoints, `if __name__ == "__main__"` modules, Typer/Click/argparse CLI entrypoints, uvicorn/gunicorn references, and package metadata console scripts relevant to backend workers/services.

## Success Criteria
- Candidate Python entrypoint modules and console-script metadata are scanned and saved with commands.
- Known queue/runtime/Cortex/sandbox/blob/logicalfs surfaces appear or their absence is explained.
- No production code is changed.

## Subproblems
- none

## Results
- R675

## Latest Check
C717

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P682/children/P687/README.md
- Ticket T680: problems/P000/children/P007/children/P668/children/P673/children/P682/children/P687/tickets/T680.md
- Result R675: problems/P000/children/P007/children/P668/children/P673/children/P682/children/P687/results/R675.md
- Check C717: problems/P000/children/P007/children/P668/children/P673/children/P682/children/P687/checks/C717.md

## Follow-ups
- none
