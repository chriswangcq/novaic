# Normalize `_err()` content to ToolOutputV1

## Problem Definition

Runtime `_err()` is the remaining tool-result path that writes raw JSON into `content`. This covers unknown tools and handler exceptions, so leaving it unchanged keeps legacy durable shape alive.

## Proposed Solution

Change `_err()` to serialize `tool_error(error).to_dict()` into `content`. Add focused assertions for unknown tool and exception paths so both continue to report status/error correctly while using `ToolOutputV1`.

## Acceptance Criteria

- `_err()` content has `version == "tool-output.v1"`.
- `_err()` content has `ok=false` and carries the error text.
- Unknown-tool path still returns `success=false`, `status=error`, and a useful top-level `error`.
- Executor exception path still logs the structured failure event and returns a useful top-level `error`.

## Verification Plan

- Run `python -m pytest tests/unit/task_queue/test_tool_handlers_failure_event.py -q`.
- Run `python -m pytest tests/test_pr234_tool_logical_failure.py tests/test_pr234_repeated_scope_mismatch.py tests/unit/task_queue/test_device_tool_handlers.py -q`.

## Risks

- Tests that assumed raw `{"error": ...}` content must be updated to the new durable envelope.

## Assumptions

- Top-level `error` remains available for task-layer handling; only durable `content` changes.
