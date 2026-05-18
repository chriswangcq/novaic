# Inventory Root RW Scratch Usage

## Problem Definition

Root `/rw/scratch` appears in Cortex workspace layout and tests, while current shell execution exposes subagent-aware `RW_SCRATCH=/cortex/rw/subagents/{subagent}/scratch`. We need a read-only inventory before changing tests or initialization.

## Proposed Solution

Run static scans for `/rw/scratch`, `RW_SCRATCH`, `/rw/subagents`, `initialize_layout`, and `scratch` in Cortex and LogicalFS. Inspect relevant slices and classify hits as current subagent-aware scratch, generic writable RW fixture, removable root scratch layout, or lower-layer generic LogicalFS authority test.

## Acceptance Criteria

- Exact commands and outputs are recorded.
- Hits are classified with file-level targets for P636.
- The result distinguishes Cortex semantic layout from LogicalFS lower-layer generic path tests.
- No code changes are made.

## Verification Plan

Use `rg` and targeted `nl/sed` slices. The check should fail if classifications are vague or if cleanup targets are not explicit.

## Risks

- Over-classifying generic arbitrary `/rw` tests as legacy scratch could cause unnecessary churn.
- Under-classifying Workspace initialization would leave the default global scratch layout in place.

## Assumptions

- P636 will perform edits after this inventory.
