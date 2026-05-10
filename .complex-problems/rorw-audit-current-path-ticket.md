# Audit Existing Shell RO/RW Mount Flow

## Problem Definition

We need a precise audit of the current shell execution path before proposing optimizations. The audit should trace Runtime shell tool execution into Cortex, describe temporary RO/RW materialization, and identify repeated costs.

## Proposed Solution

Read the focused code paths in `novaic-agent-runtime` and `novaic-cortex`, then summarize confirmed behavior with file/function evidence.

## Acceptance Criteria

- Runtime to Cortex shell call path is identified.
- Sandbox materialization and persistence logic is identified.
- Current optimizations and bottlenecks are listed.
- No implementation changes are made.

## Verification Plan

- Use `rg`/`nl` to inspect relevant functions.
- Cross-check against existing tests for sandbox persistence and limits.

## Risks

- Confusing current dirty code with intended design; use concrete file references only.

## Assumptions

- Local repository is the source of truth for this research pass.
