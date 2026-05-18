# Generation-like residue closure ticket

## Problem Definition

The previous cleanup removed the narrow session-generation defaults, but the widened guard still exposes ambiguous generation-like residue. Two hits are potentially live control-plane semantics (`session_fsm.py` event generation and `subagent_wake.py` session generation), while other hits are likely counters, round numbers, or audit/persistence adapters. Leaving them unclassified violates the explicit-boundary and AI-era cleanup goals.

## Proposed Solution

Inspect the remaining widened guard hits as a matrix, then patch the live authority/default paths and document/classify the safe counter/adapter paths in code or tests. Keep the implementation small: introduce narrowly named validators only where a field is live control-plane state; avoid turning harmless counters into over-abstracted plumbing. Add focused tests for any patched boundary, then rerun the guards and targeted suites.

## Acceptance Criteria

- `session_fsm.py` `event_generation` default is patched or explicitly classified with evidence.
- `task_queue/sagas/subagent_wake.py` `session_generation` coercion is patched or explicitly classified with evidence.
- The widened guard output has a complete classification matrix with no unclassified generation-like residue.
- Any live authority/default patch has focused regression tests.
- Narrow generation guard remains clean.
- Focused runtime tests pass after the changes.

## Verification Plan

1. Inspect `session_fsm.py`, `subagent_wake.py`, and all widened guard hits.
2. Patch live authority/default code and add tests.
3. Rerun narrow guard.
4. Rerun widened guard and record a classification matrix.
5. Rerun focused tests covering changed runtime boundaries.

## Risks

- Over-patching counters could add pointless complexity.
- Under-classifying a live path could leave the same failure mode hidden under a new name.
- Subagent wake generation may be fed by saga context, so changing validation could expose missing upstream data in tests.

## Assumptions

- No compatibility is required for missing, bool, or malformed session generation in live control-plane paths.
- Numeric counters and round numbers are acceptable only when explicitly identified as non-authority values.
