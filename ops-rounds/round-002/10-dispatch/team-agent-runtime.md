# Round 002 Dispatch - Agent Runtime Team

## Objective
Move idempotency and retry control from local workaround to robust multi-process behavior.

## Hard Tasks
1. Introduce persisted or queue-level idempotency strategy beyond in-process cache.
2. Add retry scheduling visibility (`next_retry_at` or equivalent) in queue behavior.
3. Add cross-process and restart scenario tests for duplicate task handling.
4. Publish retry/idempotency runbook aligned with API/Runtime/Tools usage.

## Acceptance Criteria
- Duplicate side effects are prevented across process boundaries.
- Retry behavior is observable and deterministic.
- Cross-process idempotency tests pass.

## Required Evidence
- implementation summary and file paths
- test commands and pass summary
- runbook path

## Status
- owner: Agent Runtime Team
- due: 2026-02-26
- status: IN_PROGRESS
