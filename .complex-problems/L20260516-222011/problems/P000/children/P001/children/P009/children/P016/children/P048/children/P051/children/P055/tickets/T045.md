# Ticket: verify displayed images survive context assembly

## Problem Definition

After `display(blob://...)`, the public tool content is allowed to be placeholder-only, but the next LLM request must still receive the displayed image as model-visible image content. The handoff must use durable payload / Cortex step projection rather than public text history.

## Proposed Solution

- Trace display durable payload through `build_save_results_tasks`, Cortex step payload reads, `step_result_projection`, `expand_messages_for_llm`, and multimodal conversion.
- Add focused tests if needed to prove a display `tool-step-payload.v1` image becomes a user image message in the next request.
- Ensure public placeholder content is ignored in favor of the durable step payload during LLM assembly.

## Acceptance Criteria

- Display durable payload with image `_mcp_content` is resolved into display perception content.
- The processed request contains provider-native image content.
- The request does not use public placeholder content as the only source of truth.

## Verification Plan

- Run focused runtime tests for display step expansion and multimodal conversion.
- Run Cortex projection tests for `tool-step-payload.v1` display payloads.
- Add/adjust tests if current coverage does not prove durable payload image preservation.

## Risks

- It is easy to accidentally satisfy tests with a mocked bridge that bypasses durable payload parsing; at least one test should cover the `tool-step-payload.v1` projection shape directly.

## Assumptions

- Provider-specific redaction/logging is handled by sibling `P056`.
