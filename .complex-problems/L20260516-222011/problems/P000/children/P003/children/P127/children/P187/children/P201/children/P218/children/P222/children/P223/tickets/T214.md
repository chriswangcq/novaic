# Search active code for removed projection symbol

## Problem Definition

The deleted `resolve_for_llm` API must not remain in active package source or tests. Any remaining references should be proven to be ledger/history only.

## Proposed Solution

Run targeted `rg` searches over active source/test package paths and separately over the whole workspace to classify any remaining matches.

## Acceptance Criteria

- Active source/test search returns no `resolve_for_llm` matches.
- Whole-workspace matches, if any, are limited to `.complex-problems` history or other non-runtime records.
- Exact commands and outputs are recorded.

## Verification Plan

Use `rg -n "resolve_for_llm"` on active package directories, then use a broader search excluding common generated/cache directories to classify residue.

## Risks

- Ledger references will appear because they document the cleanup; they should not be counted as active runtime code.

## Assumptions

- Active runtime/test packages are the top-level `novaic-*` directories and root tests/docs deliberately inspected by command scope.
