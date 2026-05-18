# Install LLM prepare authority residue guards

## Problem Definition

The runtime/Cortex LLM prepare path can regress if future code reintroduces `context.jsonl`, `read_context`, or `context/read` as the provider-message authority. Source evidence alone is not enough; the boundary needs tests that fail when final LLM message assembly bypasses the explicit Cortex prepare/read-model contract.

## Proposed Solution

Identify current guard coverage added or already present around the LLM prepare path, then fill any missing guard with focused tests. The desired guard should distinguish allowed notification-hint insertion from disallowed provider-message authority. It should also catch stale source/docs that imply `context.jsonl` is the authority for prepare.

## Acceptance Criteria

- Guard coverage is mapped to specific tests and source files.
- At least one test fails if final LLM messages come from `context.read` instead of `prepare_for_llm`.
- At least one source/static guard fails if the final `llm.call` handler starts calling `read_context`/`context.read` directly.
- Residual `context.jsonl`/`read_context` references are classified as allowed non-authority paths, tests, or stale residue to remove.
- Focused tests pass.

## Verification Plan

- Search runtime sources and tests for `context.jsonl`, `read_context`, and `context.read`.
- Inspect existing guard tests from `P157` and decide if they fully satisfy this problem.
- Add or adjust focused guards if any criterion is not covered.
- Run the relevant runtime test files and record exact commands/results.

## Risks

- Over-broad string guards can block legitimate `context.read` notification-hint logic.
- Too-narrow guards can pass while an alternate LLM assembly path regresses.
- Stale comments can mislead future agents even if runtime behavior is correct.

## Assumptions

- `P157` already proved the active runtime caller path; this ticket is about durable regression protection.
- Keeping `context.read` as an internal notification-hint topic is acceptable only if it cannot become final LLM message authority.
