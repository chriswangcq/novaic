# Ticket: clean direct-tool vocabulary in tests

## Problem Definition

Tests still contain direct-tool names. Some are correct legacy regression fixtures, but others use direct tools as generic examples in current-contract tests.

## Proposed Solution

Audit and update tests by category:

- Current-contract tests should use final harness tools or shell-first commands.
- Legacy/historical tests should keep coverage but rename helpers/data to make the legacy intent explicit.
- Guard tests should continue asserting that old direct tools are not active LLM/runtime tools.

## Acceptance Criteria

- Generic fixtures no longer use direct IM/payload/audio/subagent tool names.
- Legacy fixtures and guard allowlists are explicitly named as legacy/migrated.
- Focused test files pass.
- A scan summary classifies remaining test hits.

## Verification Plan

- Focused `rg` over test directories.
- Run changed Python test files.
- Run changed frontend test files if touched.

## Risk

Blindly deleting old names could remove important regression coverage for archived step records, tool-surface guardrails, or migration denylist behavior.
