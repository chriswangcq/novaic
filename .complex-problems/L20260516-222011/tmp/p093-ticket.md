# MCP Scripts and CI Test Residue Scan

## Problem Definition

MCP test files, repository scripts, and CI/lint test helpers may still contain stale skip/TODO/FIXME/compat/fallback/legacy wording or policy comments that hide old behavior.

## Proposed Solution

Run bounded residue scans over MCP packages plus script/CI/test helper directories, classify every hit, clean small stale wording if safe, and run focused tests or explicit no-code-change verification.

## Acceptance Criteria

- MCP and script/CI test surfaces are scanned for residue markers.
- Hits are classified as current guard/policy, harmless fixture text, or stale residue.
- Safe stale residue is removed.
- Verification is recorded with focused tests or explicit no-code-change rationale.

## Verification Plan

- `rg` scans over MCP repos, scripts, CI, and test helper paths.
- Run focused pytest/shell tests for touched or representative surfaces.
