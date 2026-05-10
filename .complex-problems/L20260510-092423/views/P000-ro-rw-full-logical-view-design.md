# P000: RO/RW Full Logical View Design

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The previous RO/RW optimization research proposed explicit mount profiles and selective hydration, but the user correctly identified a deeper semantic problem: shell behavior is not statically knowable from the command string. Scripts, eval, Python, variables, and nested shell calls can access `/cortex/ro` or `/cortex/rw` without the outer command revealing that intent.

Therefore the design must be corrected:

- Shell must always see a complete, stable logical `/cortex/ro` and `/cortex/rw` view.
- Optimization must be below the visible filesystem contract, not by guessing command behavior.
- Concurrency strategy is intentionally out of scope for now.
- RW conflict frequency should be reduced through team directory conventions:
  - per-subagent private directories;
  - shared public directory;
  - per-exec temporary directory.

## Success Criteria
- Define a corrected semantic contract for shell-visible RO/RW.
- Define RW directory layout and environment variables for self/public/tmp paths.
- Define agent behavior conventions for writing files.
- Define implementation substrate options that preserve complete logical view.
- Define staged implementation plan, tests, and invariants.
- Explicitly state what is out of scope: concurrency protocol, hard subagent ACL isolation, and command-string semantic guessing.

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
