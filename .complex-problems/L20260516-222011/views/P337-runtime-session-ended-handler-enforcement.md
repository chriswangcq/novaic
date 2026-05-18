# P337: Runtime session-ended handler enforcement

Status: done
Parent: P328
Root: P000
Source Ticket: T324 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/README.md
Ticket(s): T336

## Problem
Runtime handlers receiving session-ended/finalize tasks must enforce expected wake scope and generation before mutating Cortex, claiming messages, archiving stack, or notifying queue state. Handler-side checks are the final fail-closed boundary if stale outbox or worker delivery occurs.

## Success Criteria
- Map runtime/task handlers that process session-ended/finalize/skill-end/recovery completion.
- Verify handlers compare expected scope/generation against current root/session metadata before mutation.
- Add or identify tests for missing expected scope, missing expected generation, stale scope, stale generation, and happy path.
- Ensure stale handler calls do not append Cortex input, close a newer skill, or acknowledge/claim unrelated messages.
- Remove or flag handler paths that infer generation from current active state.

## Subproblems
- P348: Runtime finalize handler inventory
- P349: React contract positive session generation
- P350: Cortex finalize mutation identity guards
- P351: Recovery compensation finalize identity
- P352: Runtime finalize enforcement aggregate verification

## Results
- R349

## Latest Check
C371

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/README.md
- Ticket T336: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/tickets/T336.md
- Result R349: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/results/R349.md
- Check C371: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P337/checks/C371.md

## Follow-ups
- none
