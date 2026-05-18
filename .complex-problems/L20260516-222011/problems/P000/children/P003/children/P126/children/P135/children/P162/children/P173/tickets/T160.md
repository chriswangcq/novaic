# Classify context read handler residue

## Problem Definition

`context_handlers.py` exposes explicit context-read behavior. We need to prove it is a safe inspection/topic handler and not a provider-message fallback path.

## Proposed Solution

Inspect `context_handlers.py`, map payload fields and bridge calls, inventory caller topics/tests, and run focused context-read tests.

## Acceptance Criteria

- Handler source is mapped with line pointers.
- The handler's role is classified as active-safe, stale, or risky with evidence.
- Context-read tests are identified and run.
- Any provider-authority usage is fixed or split.

## Verification Plan

Run `test_context_read_by_ids.py`, `test_context_read_ordering.py`, and relevant explicit-contract guard tests.

## Risks

- Tests may validate context-read output without proving it is excluded from provider messages; classification must cite provider guard tests too.

## Assumptions

- This leaf is about the context-read handler itself; broader caller inventory remains `P175`.
