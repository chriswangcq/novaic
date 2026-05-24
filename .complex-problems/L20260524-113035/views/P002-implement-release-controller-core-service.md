# P002: Implement release-controller core service

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
Build the release-controller service that can load config, poll branch heads, plan releases, execute verification/build/publish/deploy commands, persist state, expose status APIs, and support manual trigger/promotion/rollback commands.

## Success Criteria
- Service source exists under a clear repository package.
- Configuration supports branch rules, repo path/URL, registry refs, deploy command paths, poll interval, and dry-run mode.
- State persistence records branch heads, release runs, image refs, current/previous pointers, and failures.
- API exposes health, status, branch rules, runs, trigger, promote, and rollback endpoints.
- Unit tests cover branch mapping, immutable refs, state transitions, and dry-run command planning.

## Subproblems
- P007: Release-controller config and model foundation
- P008: Release-controller persistent state store
- P009: Release-controller branch planner and command runner
- P010: Release-controller HTTP control plane
- P011: Release-controller core unit tests
- P012: Add release-controller branch head polling

## Results
- R006

## Latest Check
C008

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R006: problems/P000/children/P002/results/R006.md
- Check C006: problems/P000/children/P002/checks/C006.md
- Check C008: problems/P000/children/P002/checks/C008.md

## Follow-ups
- P012: Add release-controller branch head polling
