# P001: Release-controller discovery and architecture design

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Before implementation, define the release-controller architecture against the current NovAIC deploy substrate, API-host runtime, branch strategy, registry choice, security boundary, state model, and failure behavior.

## Success Criteria
- Current deploy/runtime substrate is inventoried.
- Branch-to-environment rules are explicit.
- Controller state model and run lifecycle are documented.
- Security boundaries for Docker socket, git access, deploy commands, and prod promotion are explicit.
- The design names what will remain outside the controller, especially nginx and service discovery.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
