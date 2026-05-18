# Remove Root RW Scratch Default Layout and Rewrite Cortex Fixtures

## Problem Definition

P635 proved that Workspace still initializes global `/rw/scratch`, while current shell scratch contract is subagent-aware `RW_SCRATCH=/cortex/rw/subagents/{id}/scratch`. Cortex tests also use `/rw/scratch` as a generic writable path, which keeps the old path looking canonical.

## Proposed Solution

Remove `/rw/scratch` from `Workspace.initialize()`. Rewrite Cortex tests that use `/rw/scratch` as a generic fixture to either `/rw/tmp` for neutral writable files or `/rw/subagents/main/scratch` when the test is about scratch semantics. Preserve lower-layer LogicalFS generic tests and current `RW_SCRATCH` env behavior.

## Acceptance Criteria

- Workspace no longer creates `/rw/scratch` by default.
- Cortex tests no longer encode root `/rw/scratch` as canonical/default scratch.
- Current subagent-aware `RW_SCRATCH` behavior remains covered.
- Focused workspace/path/runtime/sandboxd tests pass.
- Post-change scans classify any remaining `/rw/scratch` hits.

## Verification Plan

Run post-change `rg` scans for `/rw/scratch`, `RW_SCRATCH`, and `/rw/subagents`. Run focused Cortex tests: workspace, workspace limits/paths/authority, runtime/path abuse, sandboxd wiring, tool metrics/wave/hooks/chaos tests touched by fixture changes.

## Risks

- Some tests assert path normalization against specific strings; fixture updates must preserve the invariant being tested.
- `/rw/tmp` is not mounted into shell historical working set by default, so runtime tests that expect shell-visible content may need `/rw/subagents/main/scratch` or `/rw/public`.
- Do not edit LogicalFS package generic authority tests unless they become an active Cortex boundary problem.

## Assumptions

- P635 classification is accepted.
- Root `/rw/scratch` is not the intended public/default scratch contract anymore.
