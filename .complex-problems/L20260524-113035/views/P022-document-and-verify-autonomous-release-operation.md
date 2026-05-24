# P022: Document and verify autonomous release operation

Status: done
Parent: P019
Root: P000
Source Ticket: T019 (split)
Source Check: none
Package: problems/P000/children/P019/children/P022
Body: problems/P000/children/P019/children/P022/README.md
Ticket(s): T023

## Problem
After autonomous polling and the managed worktree are in place, docs and verification need to describe the operational path clearly: how to enable, pause, inspect, dry-run, and keep prod promotion separate.

## Success Criteria
- Architecture docs describe the service-owned polling loop and its safety model.
- Runbook documents enable, pause, inspect, dry-run, and worktree repair commands.
- Docs keep GitHub Actions as fallback/secondary, not the release orchestrator.
- Verification evidence is recorded for tests, guards, API-host health, loopback-only exposure, and branch polling behavior.

## Subproblems
- none

## Results
- R022

## Latest Check
C024

## Bodies
- Problem: problems/P000/children/P019/children/P022/README.md
- Ticket T023: problems/P000/children/P019/children/P022/tickets/T023.md
- Result R022: problems/P000/children/P019/children/P022/results/R022.md
- Check C024: problems/P000/children/P019/children/P022/checks/C024.md

## Follow-ups
- none
