# Normalize Runtime tool success content to ToolOutputV1

## Problem Definition

`handle_tool_execute()` currently calls `_ok()` and stores executor results as raw JSON/text in `content`. That leaves durable history dependent on each executor's ad hoc shape, including legacy fields like `_mcp_content`. The new shell/display model needs `content` to become a stable `ToolOutputV1` envelope.

## Proposed Solution

Add a small normalization helper in `task_queue.handlers.tool_handlers` that converts legacy executor results into `ToolOutputV1`:

- if the result is already `tool-output.v1`, preserve it;
- otherwise store bounded readable text in `text`;
- carry legacy dict data as a diagnostic/source field only where safe;
- keep `tool_success` and `tool_status` derived from the original executor result.

Update focused tests so they assert the new durable content envelope instead of raw executor dictionaries.

## Acceptance Criteria

- `_ok()` returns `content` containing JSON with `version == "tool-output.v1"`.
- Successful dict output is readable via the `text` field.
- Logical failure output keeps `tool_success=false` and preserves the failure message inside `ToolOutputV1.text`.
- Mounted device handler tests validate the new envelope.
- Existing Runtime tool handler failure and contract tests pass.

## Verification Plan

- Run `python -m pytest tests/test_pr234_tool_logical_failure.py tests/unit/task_queue/test_device_tool_handlers.py tests/unit/task_queue/test_tool_handlers_failure_event.py -q`.
- Run `python -m pytest tests/unit/task_queue/test_tool_output_contract.py tests/test_tool_surface_boundary.py -q`.

## Risks

- Some tests or downstream readers may assume `content` is the raw executor dict. Update only tests in this migration slice; do not add compatibility branches unless a live caller requires them.

## Assumptions

- `content` is durable tool history and may safely become `ToolOutputV1` because Cortex projection now understands `tool-output.v1`.
