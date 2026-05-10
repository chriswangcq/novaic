# P000: Dynamic device tool schema cutover to shell

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Static builtin schemas are now reduced to the core surface, but mounted HD/device tools can still be dynamically merged into LLM-visible tools during context preparation. This leaves an old direct-tool path active at runtime even though the static schema looks clean.

## Success Criteria
- Runtime no longer merges mounted device schemas into the LLM request.
- Shell exposes a generic `devicectl hd ...` capability for mounted device operations.
- The shell command can call the existing Device Service proxy using explicit env.
- Direct device executors remain internal compatibility only.
- Tests prove mounted device tools are not LLM-visible and shell device command works.

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
