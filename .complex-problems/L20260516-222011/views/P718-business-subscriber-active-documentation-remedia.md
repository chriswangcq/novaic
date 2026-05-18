# P718: Business/subscriber active documentation remediation

Status: done
Parent: P716
Root: P000
Source Ticket: T708 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P718
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P718/README.md
Ticket(s): T710

## Problem
Patch safe active stale documentation claims found by candidate disposition so Business/subscriber boundaries match the current architecture. This belongs under P716 because stale docs are the main identified remediation surface and can mislead future agents into wrong service ownership.

## Success Criteria
- Safe active stale claims about Business, Subscriber, Gateway, Entangled, Queue, Runtime, Cortex, or Device ownership are patched.
- Historical comparison text is preserved only when clearly framed as non-current behavior.
- Patched docs use current boundary language: Business owns product/domain/action hooks and internal product APIs; Subscriber drains Environment notifications into Queue; Queue owns session/task/saga FSM; Runtime executes loops; Cortex owns scope/context; Gateway is edge; Device/devicectl owns hardware actions.
- No broad compatibility claim is added.

## Subproblems
- none

## Results
- R702

## Latest Check
C746

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P718/README.md
- Ticket T710: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P718/tickets/T710.md
- Result R702: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P718/results/R702.md
- Check C746: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P707/children/P716/children/P718/checks/C746.md

## Follow-ups
- none
