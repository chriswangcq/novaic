# PR-234C — Runtime Tool Logical Failure Semantics

| Field | Value |
| --- | --- |
| Status | `[x]` |
| Parent | PR-234 |
| Scope | `novaic-agent-runtime` |

## Current State

Runtime tool execution treats only `success:false` as a failed executor result. Cortex business/logical failures commonly return `ok:false`, so a failed `skill_end` can be persisted as a completed successful tool observation.

## Objective

Normalize executor success semantics so `ok:false` and `success:false` both produce failed tool observations.

## Small Tickets

- `[x]` Update `_executor_success()` to classify `ok:false` as failure.
- `[x]` Ensure saved Cortex observations get `status=error` and `success=false` for logical failures.
- `[x]` Add Runtime tests covering `skill_end` mismatch / `ok:false`.

## Acceptance Criteria

- Tool card / Cortex step status cannot say completed-success when the tool payload says `ok:false`.
- Tests assert both `success:false` and `ok:false`.

## Verification

- `cd novaic-agent-runtime && pytest tests/test_pr234_tool_logical_failure.py`
