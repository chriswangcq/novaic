# Rename projection guard tests away from legacy endorsement

## Problem Definition

Some projection guard tests still use names and fixtures like `legacy` or `old shape`. They are valid guardrails, but the wording can make stale behavior look like a supported compatibility contract.

## Proposed Solution

Rename misleading projection guard test names and fixture labels to say unsupported/wrapped guard behavior. Preserve assertions and run the focused runtime/Cortex guard tests.

## Acceptance Criteria

- Guard tests no longer describe unsupported shapes as supported legacy contracts.
- Assertions still prove unsupported/nested image payloads do not create image messages.
- Focused guard tests pass.

## Verification Plan

Run `rg` on the touched tests for legacy/old wording and run focused Cortex/runtime projection guard tests.

## Risks

- Pure renames may be noisy if over-applied; keep changes limited to misleading projection guard language.

## Assumptions

- Historical/malformed input guard tests should remain because they prevent reintroduction of old media injection bugs.
