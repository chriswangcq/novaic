# Document and verify autonomous release operation

## Problem

After autonomous polling and the managed worktree are in place, docs and verification need to describe the operational path clearly: how to enable, pause, inspect, dry-run, and keep prod promotion separate.

## Success Criteria

- Architecture docs describe the service-owned polling loop and its safety model.
- Runbook documents enable, pause, inspect, dry-run, and worktree repair commands.
- Docs keep GitHub Actions as fallback/secondary, not the release orchestrator.
- Verification evidence is recorded for tests, guards, API-host health, loopback-only exposure, and branch polling behavior.
