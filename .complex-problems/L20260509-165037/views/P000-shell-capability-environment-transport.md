# P000: Shell capability environment transport

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Sandbox-generated commands such as `agentctl` need explicit runtime/business context in order to execute interface operations from shell. Today the Cortex shell receives Cortex auth and stable file paths, but it does not receive agent/session/business routing context such as Business URL, user id, agent id, subagent id, current scope id, or wake scope path.

Without this transport, moving `im_read`, `im_reply`, and `subagent_spawn` behind shell would be a fake cutover: commands could exist but could not perform the original behavior.

## Success Criteria
- Runtime sends an explicit allowlisted capability environment with shell requests.
- Cortex accepts and forwards only allowlisted capability environment keys into the disposable sandbox.
- Sandbox-generated commands can inspect that context without leaking ephemeral paths.
- Existing shell execution behavior remains compatible.
- Tests prove the transport is explicit and allowlisted.

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
