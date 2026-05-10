# P000: agentctl IM shell command implementation

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The final tool boundary requires IM interface tools to move behind shell, but `agentctl` currently exposes only help text. Without real `agentctl im ...` behavior, removing direct `im_read`/`im_reply` would break agent communication.

## Success Criteria
- `agentctl im read` can call the Environment IM read endpoint and checkpoint observed message ids into Cortex meta.
- `agentctl im reply` can enforce read-before-reply and reply cap using Cortex meta, then call the Environment reply endpoint.
- `agentctl im send/history/search/context` can call the matching Environment endpoints.
- Commands support file-friendly options where relevant, such as `--message-file`.
- Tests prove at least read/reply round trips through local HTTP fake endpoints from inside the shell sandbox.

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
