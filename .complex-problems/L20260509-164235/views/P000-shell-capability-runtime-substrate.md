# P000: Shell capability runtime substrate

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The tool-shell boundary design requires interface/runtime style capabilities to move into shell-accessible commands while keeping only minimal harness primitives outside shell. The current sandbox exposes stable `/cortex/ro` and `/cortex/rw`, but it does not provide a reliable generic command substrate such as `agentctl`, `runtimectl`, or `cortex`.

This leaves the architecture only partially implemented: the agent can run shell, but shell is not yet a first-class capability surface for runtime/cortex operations.

## Success Criteria
- Fresh sandbox executions have stable commands on `PATH`: `agentctl`, `runtimectl`, and `cortex`.
- `agentctl --help`, `runtimectl --help`, and `cortex payload --help` work without materializing the full RO tree.
- Commands are generated inside each disposable sandbox and read auth/config from the stable shell environment rather than leaked ephemeral paths.
- Tests prove the commands are present, stable-path-safe, and do not require RO for help/smoke usage.

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
