# P000: Make Cortex depend only on sandbox service SDK

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The current sandbox extraction still lets Cortex import `sandbox_core`, which mixes service client contracts with daemon-internal execution substrate. That violates the desired final architecture: Cortex should call sandboxd through a thin service boundary, while `sandbox_core` remains daemon/internal infrastructure for process execution and mount namespace handling.

## Success Criteria
- A new independent `novaic-sandbox-sdk` package owns sandboxd wire DTOs and HTTP client only.
- Cortex imports `sandbox_sdk`, not `sandbox_core`.
- Sandbox service imports `sandbox_sdk` for HTTP contracts and `sandbox_core` for internal execution substrate.
- `sandbox_core` no longer contains service client or wire-contract modules.
- Startup, deploy, and test scripts explicitly sync/include/test `novaic-sandbox-sdk`.
- Source scans show no `sandbox_core` import under `novaic-cortex`.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
