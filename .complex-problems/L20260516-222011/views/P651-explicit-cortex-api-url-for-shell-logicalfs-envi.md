# P651: Explicit Cortex API URL for Shell LogicalFS Environment

Status: done
Parent: P648
Root: P000
Source Ticket: T645 (spawn)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651
Body: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/README.md
Ticket(s): T646

## Problem
`Sandbox` and `MountNamespaceLogicalFS` still default `cortex_api_url` to `http://localhost:19996`, which is an implicit service URL fallback for generated shell capability commands. Even though it is not a local shell execution fallback, it can silently wire shell CLIs to the wrong API instead of requiring explicit runtime/service configuration.

## Success Criteria
- Removes `http://localhost:19996` as the default `cortex_api_url` in `Sandbox` and `MountNamespaceLogicalFS`.
- Passes the Cortex API URL explicitly from the runtime/API construction path and test helpers.
- Keeps shell capability commands fail-closed when `NOVAIC_API` is missing.
- Adds/updates regression tests proving no `/tmp/.novaic_env.json` or localhost fallback exists in CLI/shell capability paths.

## Subproblems
- P652: Remove Cortex API URL Default from Test Helper

## Results
- R641

## Latest Check
C684

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/README.md
- Ticket T646: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/tickets/T646.md
- Result R641: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/results/R641.md
- Check C682: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/checks/C682.md
- Check C684: problems/P000/children/P005/children/P554/children/P632/children/P648/children/P651/checks/C684.md

## Follow-ups
- P652: Remove Cortex API URL Default from Test Helper
