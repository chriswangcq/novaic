# P469: Session hidden input remediation

Status: done
Parent: P466
Root: P000
Source Ticket: T460 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469
Body: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/README.md
Ticket(s): T462

## Problem
Remove or explicitly inject any risky production hidden inputs found by the inventory. Decision logic in session/worker paths must be reproducible from explicit constructor/config inputs instead of reading process state or mutable globals at decision time.

## Success Criteria
- Any risky direct environment/global read in a decision path is replaced by explicit configuration or a narrow adapter-boundary read.
- Unit tests or guards prove the fixed behavior is deterministic from explicit inputs.
- No broad compatibility fallback is introduced.
- If no risky hits exist, record a source-backed no-op result with evidence.

## Subproblems
- P472: Saga decision config injection
- P473: Retained ServiceConfig boundary classification
- P474: Hidden input remediation tests and guards

## Results
- R464

## Latest Check
C492

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/README.md
- Ticket T462: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/tickets/T462.md
- Result R464: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/results/R464.md
- Check C492: problems/P000/children/P004/children/P278/children/P285/children/P466/children/P469/checks/C492.md

## Follow-ups
- none
