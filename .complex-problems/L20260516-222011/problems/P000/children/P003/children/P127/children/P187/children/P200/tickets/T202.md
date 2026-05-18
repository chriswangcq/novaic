# Clean projection test residue and legacy-contract assertions

## Problem Definition

Projection tests can accidentally preserve obsolete behavior. After production cleanup, tests must protect desired shell/display/artifact contracts rather than stale helper behavior or misleading legacy names.

## Proposed Solution

Split cleanup into stale test deletion, guard-test label review, and focused test-suite verification. Delete tests for removed APIs, preserve safety regression tests that guard malformed/historical inputs, and make naming/assertions clarify that they prevent legacy behavior rather than endorse it.

## Acceptance Criteria

- Stale tests for removed production APIs are deleted.
- Safety tests that remain are named/described as guardrails.
- Projection-related test suites pass.
- No test still imports removed `resolve_for_llm`.

## Verification Plan

Run `rg` for removed API references, inspect projection-related tests, and run focused Cortex/runtime/factory projection tests after cleanup.

## Risks

- Deleting stale tests may hide a useful behavior if the API was not truly removed, but P199 already proved production deletion.
- Over-renaming tests can create noisy diffs without improving behavior.

## Assumptions

- Tests should encode the new projection contract: shell as bounded terminal text, artifacts as manifests, display via explicit perception, and no hidden media injection.
