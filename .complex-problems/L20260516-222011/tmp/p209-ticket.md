# Audit retained projection compatibility branches

## Problem Definition

After deleting the stale helper, several old-looking projection branches remain in production. Some may be legitimate persisted-data compatibility or current display behavior; others may be stale residue. They need branch-by-branch audit and cleanup.

## Proposed Solution

Split the retained branch audit into focused child problems for nested result unwrapping, MCP image/data-url handling, and generic dict fallback. For each branch, either preserve it with explicit current/persisted-data rationale and tests or remove it with tests proving the active contract is still intact.

## Acceptance Criteria

- Every retained production compatibility branch has an explicit reason or is removed.
- No retained branch can accidentally reintroduce historical image/base64 text injection into generic context.
- Test coverage matches the branch decisions.
- Production-side projection tests pass after any edits.

## Verification Plan

Use targeted source inspection and focused tests for each branch, then rerun Cortex projection tests after all branch decisions.

## Risks

- Removing historical parsing may break old persisted step payloads.
- Keeping too much fallback can hide stale or unsafe behavior.
- Current display perception may still need image data conversion, but only on explicit display projection paths.

## Assumptions

- Persisted step payload compatibility is valuable only when the branch cannot inject media into history/current-tool text projections.
