# P680: Packaged backend launcher remediation

Status: done
Parent: P676
Root: P000
Source Ticket: T673 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P680
Body: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P680/README.md
Ticket(s): T675

## Problem
`novaic-app/src-tauri/resources/backends/start-backends.sh` and its generated apple copy appear to use an old packaged topology (`AGENT_RUNTIME_PORT=19991`, only Blob/Gateway/Agent Runtime). Determine whether this is still active, then remove/update/guard the stale packaged launcher path without editing generated output blindly.

## Success Criteria
- Source resource and generated packaged launcher copies are inspected.
- If stale and unused, they are removed or guarded against active use; if active, source is updated and generated copy handled consistently.
- No generated-only fix is left without source truth.
- Relevant resource hygiene/static tests or shell syntax checks pass.

## Subproblems
- none

## Results
- R670

## Latest Check
C712

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P680/README.md
- Ticket T675: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P680/tickets/T675.md
- Result R670: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P680/results/R670.md
- Check C712: problems/P000/children/P007/children/P668/children/P672/children/P676/children/P680/checks/C712.md

## Follow-ups
- none
