# P380: Cross-repo stale compatibility residue guard

Status: done
Parent: P339
Root: P000
Source Ticket: T368 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/README.md
Ticket(s): T375

## Problem
After runtime and Cortex targeted tests pass, cross-repo source guards must classify remaining stale compatibility residue: implicit generation defaults, current-active fallback behavior, direct active pointer mutation, and deprecated finalize/session-ended branches.

## Success Criteria
- Run cross-repo `rg` guards for finalize/session-ended generation defaults, `int(...)` coercion, active-session mutation helpers, legacy compatibility names, and remaining-stack/archive synthesis.
- Classify every guard hit as safe test coverage, safe adapter signature, fixed live residue, or follow-up problem.
- No live path remains that silently defaults generation or clears/restarts/archives a newer active session from stale input.
- The result contains a concise guard matrix with file evidence.

## Subproblems
- P385: Close residual live generation coercions

## Results
- R369

## Latest Check
C412

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/README.md
- Ticket T375: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/tickets/T375.md
- Result R369: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/results/R369.md
- Check C392: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/checks/C392.md
- Check C412: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/checks/C412.md

## Follow-ups
- P385: Close residual live generation coercions
