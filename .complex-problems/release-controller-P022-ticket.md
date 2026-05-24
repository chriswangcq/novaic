# Autonomous release operation docs and final verification

## Problem Definition

Autonomous polling is now implemented and deployed, but the runbooks must clearly explain how to inspect, enable, pause, dry-run, and keep prod promotion separate.

## Proposed Solution

Update release-controller architecture and deployment runbook docs with the current deployed state:

- autonomous polling status and safety model
- enable/pause commands
- inspection commands
- dry-run behavior and non-dry-run gate
- worktree repair/update commands

Then run final local and API-host verification and record the evidence.

## Acceptance Criteria

- Docs describe service-owned polling.
- Docs show enable/pause/inspect procedures.
- Docs keep GitHub Actions as fallback.
- Docs keep prod promotion separate from branch polling.
- Final verification evidence is recorded.

## Verification Plan

- Patch docs.
- Run release-controller tests, release-controller CI guard, root pytest, and `bash -n deploy`.
- Check API-host health/status/polling/worktree one more time.

## Risks

- Docs can drift from deployed state quickly; use concrete commands and current digest/commit.

## Assumptions

- Current deployed state remains digest `sha256:9ebe598d...` and worktree commit `78411ddc0bbf`.
