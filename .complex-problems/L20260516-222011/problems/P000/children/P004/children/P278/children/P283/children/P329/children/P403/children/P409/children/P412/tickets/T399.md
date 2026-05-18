# React contract classification ticket

## Problem Definition

React contract files contain guard hits for round numbers, retry counters, stack depth, and session_generation. These must be classified so session identity stays explicit while non-session counters remain intentional.

## Proposed Solution

Inspect `task_queue/contracts/react_think.py` and `task_queue/contracts/react_actions.py`, classify all guard hits, patch any session_generation fallback, and run focused explicit-contract tests.

## Acceptance Criteria

- `session_generation` is required and positive in React contract inputs.
- No `session_generation` fallback to `0` or `1` remains.
- `round_num`, `no_tool_retry_count`, `stack_hold_retry_count`, `repeated_tool_error_count`, and `stack_depth` hits are classified as loop counters or patched if unsafe.
- Focused contract tests pass.

## Verification Plan

- Run targeted `rg` guard over the two contract files.
- Inspect source around all hits.
- Run `tests/test_runtime_explicit_contracts.py`.

## Risks

- Round/retry counters are legitimate agent loop state; avoid deleting them just because they match broad numeric fallback guards.

## Assumptions

- Session generation must be explicit and positive for React think/actions.
