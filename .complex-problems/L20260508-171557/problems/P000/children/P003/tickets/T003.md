# T003 Task Execution Policy Tables

## Problem Definition

`TaskExecutionEngine._execute_task(...)` still embeds idempotency branch handling and failure/retry effect construction inside one imperative method. The behavior is correct but not yet a small deterministic policy surface: duplicate completion, in-progress contention, business error, retryable error, and success all need explicit decision helpers that can be tested from input snapshots.

## Proposed Solution

- Add a task execution policy module with explicit dataclasses/functions for:
  - idempotency guard decision classification
  - successful handler completion effects
  - business error failure effects
  - retryable/unretryable exception failure effects
- Keep protocol effect execution in `TaskExecutionEngine`, but move payload/branch calculation into pure helpers.
- Update `TaskExecutionEngine` to consume the policy outputs and call the P002 `EffectPlanRunner`.
- Add focused tests for the pure policy boundary.

## Verification Plan

- Run new policy tests for duplicate completed, in-progress contention, success, business error, retryable error, and exhausted retry.
- Run task execution unit tests and effect-boundary tests.
- Scan `task_execution.py` to ensure direct effect execution remains absent.

## Acceptance Criteria

- Task idempotency/failure decisions are covered by pure helper tests.
- `TaskExecutionEngine` delegates decision construction to the policy module.
- `TaskExecutionEngine` still uses `EffectPlanRunner` from P002 and has no `execute_effect` residue.
- Existing task execution tests remain green.
