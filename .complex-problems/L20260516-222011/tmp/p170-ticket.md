# Audit LLM payload handoff regression coverage

## Problem Definition

The source mapping is only useful if regression coverage catches future drift. We need a focused audit of tests that would fail if prepare-context output stopped being the sole authority for provider messages/tools across the saga-builder, handler, and provider-contract path.

## Proposed Solution

Inventory current tests, identify the precise regressions they catch, add a missing direct guard if needed, then run the focused runtime test slice.

## Acceptance Criteria

- Existing tests covering prepare-result-to-LLM handoff are listed with line pointers.
- The audit states which plausible regression each test catches.
- Missing direct coverage is added or split into a follow-up if too broad.
- Focused runtime tests are run and reported.

## Verification Plan

Run explicit-contract, prepare-context smoke guardrail, wake child scope, and saga DAG tests. Use source/test line pointers rather than generic claims.

## Risks

- Coverage can be broad but still not catch the exact “old context becomes provider authority” failure mode.

## Assumptions

- This ticket may be one-go only if the existing plus newly added tests already cover the full handoff path after `P168` and `P169` improvements.
