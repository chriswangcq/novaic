# Legacy DFS deletion inventory

## Problem Definition

Before deleting legacy DFS files, identify every remaining `ContextEngine` / `StepTree` / DFS test usage and decide whether it is active production, debug-only, projection-artifact verification, or immediately removable.

## Proposed Solution

- Run static scans for `ContextEngine`, `StepTree`, `prepare_messages_for_llm`, `read_context`, `context.jsonl`, `steps`, and `summary.md`.
- Build a file-by-file classification.
- Decide which files should be deleted now, which must be migrated first, and which are not part of the DFS source problem.
- Record exact deletion/migration candidates for follow-up execution.

## Acceptance Criteria

- A deletion inventory exists with exact file paths.
- No active production/API/runtime DFS read dependency remains unclassified.
- The next cleanup ticket can act from the inventory without rediscovery.

## Verification Plan

- Static scans are included in the result.
- Cross-check with existing source guards for prepare/status active paths.

## Risks

- Some materialized artifact helpers are still used by write-side projection tests; do not misclassify them as DFS fallback.

## Assumptions

- P058 is inventory only; physical deletion happens in child/follow-up ticket if the inventory finds migration work.
