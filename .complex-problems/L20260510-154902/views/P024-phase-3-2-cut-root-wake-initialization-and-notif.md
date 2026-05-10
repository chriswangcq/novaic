# P024: Phase 3.2: Cut root/wake initialization and notifications to events

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P024
Body: problems/P000/children/P004/children/P024/README.md
Ticket(s): T022

## Problem
Root and wake initialization plus attached input notifications must append ContextEvents as authoritative facts. Legacy scope files may still be emitted only as projection/debug artifacts during the transition.

## Success Criteria
- Root/wake creation appends `RootInitialized` and `WakeStarted` events.
- Input notification attachment appends `InputNotificationAttached` events.
- Event payloads contain enough explicit information to rebuild notification hints and active wake stack.
- Tests verify event stream contents for these paths.

## Subproblems
- P029: Phase 3.2.1: Emit root and wake lifecycle events
- P030: Phase 3.2.2: Emit notification attachment events
- P031: Phase 3.2.3: Verify root/wake/notification cutover boundaries

## Results
- R023

## Latest Check
C025

## Bodies
- Problem: problems/P000/children/P004/children/P024/README.md
- Ticket T022: problems/P000/children/P004/children/P024/tickets/T022.md
- Result R023: problems/P000/children/P004/children/P024/results/R023.md
- Check C025: problems/P000/children/P004/children/P024/checks/C025.md

## Follow-ups
- none
