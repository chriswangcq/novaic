# P682: Entrypoint discovery scan artifacts

Status: done
Parent: P673
Root: P000
Source Ticket: T677 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P682
Body: problems/P000/children/P007/children/P668/children/P673/children/P682/README.md
Ticket(s): T678

## Problem
Locate backend worker/service entrypoint files and launch commands from repository source, scripts, package metadata, app resources, and deployment/config files. Produce reproducible scan artifacts so later classification is evidence-based and not memory-based.

## Success Criteria
- Repository scans capture candidate Python modules, shell scripts, package scripts, app resources, service configs, and deploy/worker launch commands.
- Candidate artifacts are saved under `.complex-problems/L20260516-222011/tmp/` with the commands used.
- High-noise outputs are summarized with stable pointers instead of pasted wholesale.
- No production code is changed in this discovery-only child.

## Subproblems
- P686: Script and package entrypoint scan
- P687: Python module and CLI entrypoint scan
- P688: Config and deployment launch reference scan

## Results
- R677

## Latest Check
C719

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P682/README.md
- Ticket T678: problems/P000/children/P007/children/P668/children/P673/children/P682/tickets/T678.md
- Result R677: problems/P000/children/P007/children/P668/children/P673/children/P682/results/R677.md
- Check C719: problems/P000/children/P007/children/P668/children/P673/children/P682/checks/C719.md

## Follow-ups
- none
