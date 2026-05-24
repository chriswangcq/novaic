# Update release-controller CI/CD docs

## Problem Definition

Release-controller documentation describes the intended architecture but does not yet reflect the implemented/deployed state, operator endpoints, image deploy command, and current managed-worktree limitation.

## Proposed Solution

Patch `docs/architecture/release-controller.md` and, if useful, deployment runbook docs to include:

- current deployed API host status
- loopback-only endpoint and health/status checks
- self-hosted branch-driven flow as the desired long-term path
- image-based deployment command
- dry-run/manual trigger/promotion/rollback behavior
- current limitation that non-dry-run branch releases need a managed worktree checkout

## Acceptance Criteria

- Docs do not describe GitHub Actions as the long-term primary orchestrator.
- Docs mention the deployed controller service and loopback endpoint.
- Docs include deploy command and immutable digest usage.
- Docs mention dry-run default and managed worktree gap.
- Docs avoid claiming public controller ingress.

## Verification Plan

- Patch docs.
- Search for required markers.
- Run release-controller CI guard.

## Risks

- Overstating autonomous deployment would mislead future operators.

## Assumptions

- Full worktree automation will be handled after this ledger if needed.
