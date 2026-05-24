# P019: Enable autonomous branch polling and managed staging release path

Status: followup
Parent: P000
Root: P000
Source Ticket: none (none)
Source Check: C020
Package: problems/P000/children/P019
Body: problems/P000/children/P019/README.md
Ticket(s): T019

## Problem
The deployed release-controller can poll branch heads through `/v1/polls/once`, but the root CI/CD goal requires the controller itself to own branch-driven release orchestration. Add a service-owned polling loop that uses `poll_interval_seconds`, bootstrap and verify the API-host managed worktree, and keep prod protected from branch-triggered automation.

## Success Criteria
- Release-controller has an internal polling loop or equivalent service-owned scheduler that periodically invokes `BranchPoller`.
- The loop is explicitly configurable and test-covered.
- API-host `/opt/novaic/release-controller/worktree` is a verified git checkout with submodules ready for release commands.
- Deployed controller can observe branch heads from its own configured repo path.
- Branch-triggered automation can only target non-prod namespaces; prod remains promotion-only.
- Operational docs show how to enable, verify, pause, and inspect autonomous polling.

## Subproblems
- P020: Add autonomous release-controller polling loop
- P021: Bootstrap API-host worktree and redeploy controller
- P022: Document and verify autonomous release operation

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P019/README.md
- Ticket T019: problems/P000/children/P019/tickets/T019.md

## Follow-ups
- none
