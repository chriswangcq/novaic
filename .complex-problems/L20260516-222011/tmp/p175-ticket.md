# Inventory runtime read_context callers and guard coverage

## Problem Definition

After classifying the handler and wake continuity paths, we still need a full inventory of runtime `read_context` / `context.read` occurrences to ensure no production caller remains unclassified or able to influence provider messages.

## Proposed Solution

Run targeted search over runtime task_queue and tests, classify every production caller, map corresponding guard tests, and fix or split any unclassified active path.

## Acceptance Criteria

- Runtime production `read_context` / `context.read` occurrences are inventoried and classified.
- Test-only occurrences are grouped by purpose rather than mistaken for active code.
- Provider non-authority guards are listed and run.
- Any unclassified production caller is fixed or split.

## Verification Plan

Use `rg` inventory plus focused tests: context-read by-id/order, PR-85 prepare guardrails, runtime explicit contracts, and no-wake replay.

## Risks

- `context.read` appears in comments and docs; classification must not overreact to comments but must not ignore active topic handlers.

## Assumptions

- This is the closing inventory leaf for `P162`.
