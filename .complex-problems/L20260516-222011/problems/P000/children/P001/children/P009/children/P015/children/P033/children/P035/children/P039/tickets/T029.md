# Ticket: clean runtime test direct-tool fixtures

## Problem Definition

Runtime tests still mention `im_reply` and `im_read`. Some uses are valid legacy-negative fixtures, while activity projection fixtures still display archived direct-tool behavior.

## Proposed Solution

Separate runtime test cleanup into smaller buckets:

- Finalizer tests: ensure legacy direct IM reply fixtures are named as legacy-negative cases and current success paths use shell `agentctl`.
- Activity projection tests: align with monitor legacy-boundary work and avoid presenting direct IM tools as current behavior.
- Smoke/guard tests: keep negative assertions explicit.

## Acceptance Criteria

- Runtime current-path tests use shell-first examples.
- Legacy direct-tool fixtures are explicitly named/commented as legacy-negative archived data.
- Focused runtime tests pass.

## Verification Plan

- Focused `rg` over `novaic-agent-runtime/tests`.
- Run touched runtime tests.

## Risk

Activity projection cleanup overlaps with `P036`; avoid duplicating work or prematurely closing the monitor-specific boundary problem.
