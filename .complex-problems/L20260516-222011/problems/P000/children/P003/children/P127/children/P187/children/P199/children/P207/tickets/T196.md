# Inventory `resolve_for_llm` live callers and exports

## Problem Definition

The stale projection helper should only be deleted after a fresh, explicit caller/export inventory proves it is not used by live production paths.

## Proposed Solution

Use `rg` and focused source inspection to find every in-repo reference to `resolve_for_llm`, inspect package exports and tests that may pin the API, and record whether production deletion is safe.

## Acceptance Criteria

- All `resolve_for_llm` references are listed by file/path role.
- Production caller status is stated explicitly.
- Export cleanup needs are identified.
- The next deletion ticket has concrete file targets.

## Verification Plan

Run `rg "resolve_for_llm"` across the repository and inspect the relevant source/export/test files around each match.

## Risks

- Dynamic external imports cannot be proven by static in-repo search.
- Tests may intentionally preserve stale API behavior unless removed in a later cleanup ticket.

## Assumptions

- In-repo references are the authoritative deletion boundary for this cleanup.
