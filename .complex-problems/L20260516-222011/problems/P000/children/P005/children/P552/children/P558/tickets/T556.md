# Map LogicalFS Sandbox Blob Entry Points And Tests

## Problem Definition

P558 must identify CLI/service entrypoints and tests covering LogicalFS, sandbox, blob, and Cortex boundary behavior.

## Proposed Solution

Run targeted file/test discovery and inspect entrypoint files. Produce a map of runnable service/CLI surfaces and test files relevant to P005 verification.

## Acceptance Criteria

- Lists service/CLI entrypoints.
- Lists relevant tests.
- Records discovery commands and artifacts.
- Identifies immediate coverage gaps for P555.

## Verification Plan

Use `rg --files`, `find`, and bounded source reads. No code changes.

## Risks

- Some deployment scripts may live outside these modules.
- Test names can lag current behavior.

## Assumptions

- Local tests are the primary verification surface for this branch.
