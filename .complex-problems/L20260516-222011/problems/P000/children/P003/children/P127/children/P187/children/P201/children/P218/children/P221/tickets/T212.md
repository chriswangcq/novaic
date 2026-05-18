# Execute focused Cortex/runtime/factory regression tests

## Problem Definition

The projection cleanup branch needs a final focused test chain to ensure Cortex projection, runtime context assembly, and factory provider/log behavior remain green together.

## Proposed Solution

Run the three focused pytest commands that cover the changed projection surface. Record exact commands and outcomes.

## Acceptance Criteria

- Cortex projection tests pass.
- Runtime no-historical-image and factory-client multimodal tests pass.
- Factory chat/log tests pass.
- Any failure is captured as an execution result and not ignored.

## Verification Plan

Run:

- `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_tool_output_projection.py novaic-cortex/tests/test_step_result_projection.py`
- `PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py novaic-agent-runtime/tests/unit/task_queue/test_factory_client_multimodal.py`
- `pytest -q novaic-llm-factory/tests/test_chat_routes.py novaic-llm-factory/tests/test_log_routes.py`

## Risks

- Environment import paths must be set explicitly for packages that are not installed in editable mode.

## Assumptions

- Focused regression scope is sufficient for projection-chain closure; broad unrelated suites are outside this ticket.
