# P021: Bootstrap API-host worktree and redeploy controller

Status: doing
Parent: P019
Root: P000
Source Ticket: T019 (split)
Source Check: none
Package: problems/P000/children/P019/children/P021
Body: problems/P000/children/P019/children/P021/README.md
Ticket(s): T021

## Problem
The API host has the release-controller deployed, but real release commands need `/opt/novaic/release-controller/worktree` to be a managed git checkout with submodules. Bootstrap or repair that checkout, then redeploy the updated release-controller image.

## Success Criteria
- API-host worktree is a git checkout for `https://github.com/chriswangcq/novaic.git`.
- Submodules needed by the backend and Factory build contexts are initialized.
- Release-controller image is rebuilt, pushed to the API-host registry, and deployed by immutable digest.
- Deployed controller remains loopback-only and healthy.
- Deployed controller can observe branch heads using its configured repo/worktree.
- Existing prod/staging API and Factory health checks still pass.

## Subproblems
- P023: Publish platform release source to main

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/children/P019/children/P021/README.md
- Ticket T021: problems/P000/children/P019/children/P021/tickets/T021.md

## Follow-ups
- none
