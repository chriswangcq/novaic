# Verify RW Scratch Cleanup Residue

## Problem Definition

After removing Workspace default `/rw/scratch` and rewriting Cortex test fixtures, the repo needs a final scan to ensure root scratch is no longer a Cortex default/canonical path. Any remaining hits must be lower-layer generic tests or explicit follow-up candidates.

## Proposed Solution

Run full scans for `/rw/scratch`, `rw/scratch`, `RW_SCRATCH`, and `/rw/subagents` across Cortex and LogicalFS. Classify remaining hits and run focused tests covering the rewritten areas plus LogicalFS layout tests.

## Acceptance Criteria

- Full scans are recorded.
- Remaining root `/rw/scratch` hits are classified as lower-layer/out-of-scope or follow-up-worthy.
- Cortex code/tests no longer advertise root `/rw/scratch` as default/canonical scratch.
- Focused tests pass.

## Verification Plan

Run `rg` scans and focused test suites for Cortex workspace/path/runtime/sandboxd tests plus LogicalFS tests that still contain generic scratch fixtures.

## Risks

- If Cortex still contains `/rw/scratch`, this should become a follow-up rather than being waved away.
- LogicalFS lower-layer tests may still use scratch generically; classify precisely.

## Assumptions

- P638/P639 are complete and their checks are trusted.
