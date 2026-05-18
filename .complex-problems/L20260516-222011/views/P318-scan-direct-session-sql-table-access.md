# P318: Scan direct session SQL table access

Status: done
Parent: P293
Root: P000
Source Ticket: T307 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P318
Body: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P318/README.md
Ticket(s): T308

## Problem
Find direct SQL/table access for session state, active session, inbox, and outbox tables. Classify whether matches are legitimate repository/adapter code, tests, docs, or risky active paths outside the intended boundary.

## Success Criteria
- Search patterns and representative matches are recorded.
- Production matches are classified by owner module and boundary legitimacy.
- Any direct production SQL outside the intended repository/ledger/outbox adapter boundary is flagged for cleanup.

## Subproblems
- none

## Results
- R302

## Latest Check
C321

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P318/README.md
- Ticket T308: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P318/tickets/T308.md
- Result R302: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P318/results/R302.md
- Check C321: problems/P000/children/P004/children/P278/children/P282/children/P287/children/P293/children/P318/checks/C321.md

## Follow-ups
- none
