# P004: Verify and clean up reasoning streaming end to end

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T011

## Problem
The streaming change touches multiple repos and can regress non-streaming LLM calls, saga decisions, projection privacy, or App monitor UX. The final pass must prove the path and clean up any transitional or misleading code residue.

## Success Criteria
- Focused tests pass in all touched repos.
- Cross-boundary contracts are documented or represented by tests clearly enough for future agents.
- Diff review shows no long-term fallback branch, no stale misleading path, and no accidental raw partial reasoning in LLM input history.
- The ledger contains evidence, stress testing, residual risk, and result IDs for closure.

## Subproblems
- P012: Run focused cross-repo reasoning streaming verification
- P013: Review streaming contracts and remove misleading residue
- P014: Prepare final closure evidence for reasoning streaming construction

## Results
- R013

## Latest Check
C013

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T011: problems/P000/children/P004/tickets/T011.md
- Result R013: problems/P000/children/P004/results/R013.md
- Check C013: problems/P000/children/P004/checks/C013.md

## Follow-ups
- none
