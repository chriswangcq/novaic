# Business service and subscriber boundary classification result

## Summary

Completed the Business/subscriber boundary classification branch. Discovery mapped Business/subscriber responsibilities, and remediation patched active stale docs/code wording plus verified focused guardrails. Business remains product/domain/action-hook owner; Subscriber remains Environment notification drain into Queue; Queue/Runtime/Cortex/Gateway/Device ownership stays separated.

## Done

- `P715/R700`: Discovered Business/subscriber entrypoints, launch surfaces, roles, dependencies, hidden config candidates, and cleanup candidates.
- `P716/R705`: Reviewed and patched active residue, including docs around Gateway/Business/Entangled product CRUD and Business code wording around subagent ownership/logging.
- Confirmed subscriber aggregation config is explicit at process boundary and injected into grouping logic.
- Confirmed subscriber does not own Cortex scope input or wake/session lifecycle.

## Verification

- Child checks passed: P715/C744 and P716/C749.
- Focused Business tests passed: `test_im_aggregation.py`, `test_pr153_lifecycle_guardrails.py`, `test_pr117_task_proxy_removed.py`.
- Architecture/lifecycle/startup lints passed: docs status consistency, lifecycle loop ownership, start config contract.
- Focused residue scans were run and classified.

## Known Gaps

- Historical roadmap/ticket text remains as archive and is not current guidance.
- Broader pre-existing dirty worktree changes outside this branch were not touched.

## Artifacts

- Child results: R700, R705.
- Changed docs: `docs/entangled-architecture.md`, `docs/gateway/rest-auth-and-deps.md`.
- Changed Business code wording: `novaic-business/business/internal/helpers.py`, `novaic-business/business/internal/subagent.py`.
