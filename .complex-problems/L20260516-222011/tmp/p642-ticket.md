# Rewrite Runtime and Tool Root Scratch Fixtures

## Problem Definition

Runtime/tool tests still use root `/rw/scratch` as generic fixture paths. Some of these are Cortex-only read/write tests; others may require shell-visible RW working set behavior. They must be updated without changing the invariant being tested.

## Proposed Solution

Update runtime/tool/metrics/chaos/wave fixture paths from `/rw/scratch` to current paths. Use `/rw/subagents/main/scratch` when the fixture needs to reflect shell-visible scratch behavior; use `/rw/tmp` or `/rw/public` for pure Cortex read/write metrics probes where shell visibility is irrelevant.

## Acceptance Criteria

- Target runtime/tool test files no longer use root `/rw/scratch`.
- Tests preserve truncation, metrics, hooks, chaos, and read/write behavior.
- Focused tests for touched files pass.

## Verification Plan

Run scans for `/rw/scratch` in target files and focused tests for `test_runtime.py`, `test_cortex_chaos.py`, `test_hooks_limits.py`, `test_tool_metrics.py`, and `test_wave4_metrics.py`.

## Risks

- Runtime tests with pre-populated store keys must use a path whose object key matches Workspace authority mapping.
- Using `/rw/tmp` in a shell-visible test would be wrong if the historical `/rw/tmp` tree is intentionally not mounted.

## Assumptions

- These files do not intentionally test path abuse/traversal; P643 owns that class.
