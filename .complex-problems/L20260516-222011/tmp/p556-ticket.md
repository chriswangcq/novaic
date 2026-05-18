# Inventory LogicalFS Sandbox Blob Modules

## Problem Definition

P556 must identify the local file/module universe relevant to LogicalFS, sandbox, Cortex, and blob layering.

## Proposed Solution

Run read-only filesystem discovery and targeted filename searches from the workspace root. Record repository/module roots, key service/core/CLI files, and any expected module names that are absent locally.

## Acceptance Criteria

- Discovery commands are recorded.
- Relevant root directories are listed.
- Key service/core/CLI files are listed.
- Missing expected modules are noted.

## Verification Plan

Use `find`, `rg --files`, and bounded `ls` output. Re-check that reported roots actually exist.

## Risks

- Separate GitHub repos may not be checked out under this root.
- File names may not contain expected keywords.

## Assumptions

- Local checkout reflects the currently integrated backend code enough for this inventory.
