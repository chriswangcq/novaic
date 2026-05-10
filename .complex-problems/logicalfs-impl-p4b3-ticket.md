# Prove Blob Boundary Scanner Positive And Negative Behavior

## Problem Definition

The scanner passes the current tree, but it must also prove that it permits known-good snippets and rejects known-bad live `RO` / `RW` bypass snippets. Without negative proof, the guardrail could be wired incorrectly while still passing.

## Proposed Solution

Add tests that feed the P010 synthetic `ALLOWED_SNIPPETS` and `FORBIDDEN_SNIPPETS` through the same scanner helper functions used by the source-tree tests.

## Acceptance Criteria

- Allowed snippets produce no violations.
- Forbidden snippets produce direct object authority violations.
- The targeted guardrail test file passes.

## Verification Plan

- Run `tests/test_blob_boundary_guard.py`.

## Risks

- Synthetic snippets must use the same policy path normalization as real source files.

## Assumptions

- P011 scanner helpers are intentionally importable/testable inside the same test module.
