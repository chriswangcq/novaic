# P807: Dev Startup Port And Service URL Contract Remediation

Status: done
Parent: P805
Root: P000
Source Ticket: T796 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P807
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P807/README.md
Ticket(s): T799

## Problem
The dev startup script names port `19996` as `PORT_CORTEX`, while app service config names the same port `vmcontrol`. Runtime worker commands also pass `--cortex-url "$CORTEX_URL"`, so the dev graph is ambiguous about whether `19996` is Cortex or VMControl.

## Success Criteria
- `novaic-app/scripts/start-backends.sh` no longer labels `19996` as Cortex unless it actually starts or expects Cortex there.
- Worker `--cortex-url` arguments remain explicit and are either derived from an explicitly named Cortex URL override/default or documented as requiring an external Cortex service.
- The status/startup text accurately describes what the dev script starts and what must run separately.
- Targeted scans for `PORT_CORTEX`, `CORTEX_URL`, `vmcontrol`, and `--cortex-url` show no ambiguous port naming.
- `bash -n novaic-app/scripts/start-backends.sh` passes.

## Subproblems
- none

## Results
- R788

## Latest Check
C836

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P807/README.md
- Ticket T799: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P807/tickets/T799.md
- Result R788: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P807/results/R788.md
- Check C836: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P802/children/P805/children/P807/checks/C836.md

## Follow-ups
- none
