# P327: Attach expected-generation validation audit

Status: done
Parent: P283
Root: P000
Source Ticket: T317 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P327
Body: problems/P000/children/P004/children/P278/children/P283/children/P327/README.md
Ticket(s): T319

## Problem
Audit attach delivery end to end: dispatch decision, session outbox payload, outbox worker delivery, and saga/task handler validation. Verify stale attach input cannot be delivered to or mutate a newer session generation.

## Success Criteria
- Map attach request creation and payload fields, including expected generation, with file references.
- Verify outbox worker and downstream handler preserve and enforce expected generation.
- Identify whether missing-generation or stale-generation attach payloads are rejected, ignored, or accepted.
- Add or identify tests proving stale attach does not publish/mutate the wrong wake.

## Subproblems
- P330: Attach repository payload generation audit
- P331: Attach session outbox delivery audit
- P332: Runtime attach handler generation enforcement audit
- P333: Attach stale and missing generation regression coverage audit

## Results
- R319

## Latest Check
C340

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P327/README.md
- Ticket T319: problems/P000/children/P004/children/P278/children/P283/children/P327/tickets/T319.md
- Result R319: problems/P000/children/P004/children/P278/children/P283/children/P327/results/R319.md
- Check C340: problems/P000/children/P004/children/P278/children/P283/children/P327/checks/C340.md

## Follow-ups
- none
