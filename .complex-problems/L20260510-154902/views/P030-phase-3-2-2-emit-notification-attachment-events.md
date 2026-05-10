# P030: Phase 3.2.2: Emit notification attachment events

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P004/children/P024/children/P030
Body: problems/P000/children/P004/children/P024/children/P030/README.md
Ticket(s): T024

## Problem
Environment notification hints are currently represented as legacy context rows. The authoritative fact must become `InputNotificationAttached` events with enough data for replay to recreate the hint.

## Success Criteria
- Notification attachment path appends `InputNotificationAttached`.
- Event payload includes notification id, source kind, and target scope id.
- Tests verify event stream content and replayed notification hint.
- Direct legacy context rows for notification hints are not treated as source-of-truth.

## Subproblems
- none

## Results
- R021

## Latest Check
C023

## Bodies
- Problem: problems/P000/children/P004/children/P024/children/P030/README.md
- Ticket T024: problems/P000/children/P004/children/P024/children/P030/tickets/T024.md
- Result R021: problems/P000/children/P004/children/P024/children/P030/results/R021.md
- Check C023: problems/P000/children/P004/children/P024/children/P030/checks/C023.md

## Follow-ups
- none
