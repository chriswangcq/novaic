# Audit active LogicalFS and legacy RO/RW paths

## Problem Definition

The repository already contains LogicalFS and sandboxd code, but the active
execution path must be proven from source and tests. We also need to find
remaining direct Blob or local sandbox paths that can still behave as live
`RO` / `RW` authorities.

## Proposed Solution

Inspect the current source tree with focused scans and file reads:

- Cortex shell execution and sandbox facade.
- Cortex workspace/store persistence.
- LogicalFS substrate/provider.
- Sandbox service and SDK.
- Blob object API clients and direct object calls.
- Deployment and test scripts.

Classify findings into target path, transitional accepted path, legacy inactive
path, or blocking implementation gap.

## Acceptance Criteria

- Active shell path is documented with source pointers.
- Direct Blob/object paths relevant to live `RO` / `RW` are listed.
- Fallback or bypass risks are listed.
- The result identifies the exact child problems that need code changes.

## Verification Plan

Run focused `rg` scans, inspect source files by line number, and record evidence
in the result body.

## Risks

- Large repository scans can include unrelated app/vendor files; use focused
  globs to avoid false positives.

## Assumptions

- This audit is read-only except for ledger files.
