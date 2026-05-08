# Verify Production Runtime Topology

## Problem Definition

The deployment completed successfully, but the audit needs durable evidence that production is actually running the expected service and worker topology after restart.

## Proposed Solution

Run production status and fresh-smoke commands, capture the role-level runtime worker counts, and compare them against the code-defined roster. Record any mismatch as a blocker or follow-up.

## Acceptance Criteria

- Production backend status reports all required services and workers.
- Fresh-smoke logs are current after the deploy.
- Runtime roster expected worker roles match observed process counts.
- Evidence is recorded in the ledger result.

## Verification Plan

- Run `./deploy status`.
- Run `./deploy fresh-smoke`.
- Inspect local runtime roster command output.
- Compare expected worker roles with observed status output.

## Risks

- Remote checks can be briefly transient immediately after restart; rerun status once if the first check is ambiguous.

## Assumptions

- `./deploy services` completed immediately before this audit and is the deployment baseline.
