# Cortex context projection and payload boundary audit

## Problem Definition

Cortex context assembly has recently moved toward pointer-oriented payloads, blob artifacts, LogicalFS-backed RO/RW, and provider-native media projection. The remaining risk is that implementation layers may still disagree about where large data belongs: shell/history should carry bounded terminal text and durable references, display/current-round vision should use media-native content, and historical context should remain manifest-only.

This ticket audits and optimizes the active context projection paths so large payloads, screenshots, base64 images, and long tool outputs cannot accidentally flow back into LLM text context after being externalized.

## Proposed Solution

Map the active context assembly chain from Cortex event/write APIs through step result projection and agent-runtime context preparation:

- Cortex context/event store and workspace write paths.
- Step result projection formatting for shell, display, payload, and image artifacts.
- Payload read/search/summarize/qa boundaries.
- Agent-runtime step result client and context preparation.
- Provider-native multimodal adapter boundary.

Then verify each boundary against the intended contract:

- Shell tool result in LLM history is terminal-style bounded text only.
- Long/full payload is available by step/payload reference, not inline history text.
- Display current-round image can be projected as provider-native image content.
- Display historical result is manifest/text only, with no image/base64 reinjection.
- Blob/artifact manifests stay metadata-only unless an explicit current-round visual projection path consumes them.
- Active skill stack/system messages do not break current-round media projection ordering.

Fix active leakage or stale fallback paths found during the audit. If any subarea is too large or ambiguous, split it into a child problem before implementing.

## Acceptance Criteria

- Current context assembly code paths are documented with concrete file/function pointers.
- Shell, display, payload, and provider-native image boundaries are each classified as active, compatibility-only, or dead/stale.
- Any active base64/large-output leakage into text context is removed.
- Current-round display/image projection is covered by targeted tests.
- Historical tool-output behavior is covered by manifest-only/no-base64 tests.
- Payload APIs remain accessible through explicit references and do not require inline context expansion.
- No duplicate old projection branch remains active after replacement.

## Verification Plan

- Run focused Cortex projection tests:
  - `novaic-cortex/tests/test_tool_output_projection.py`
  - `novaic-cortex/tests/test_step_result_projection.py`
  - `novaic-cortex/tests/test_resolve_for_llm.py`
  - `novaic-cortex/tests/test_payload_inspection_api.py`
- Run focused agent-runtime context tests:
  - `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_display_chat_history.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
- Perform source sweeps for high-risk terms and classify remaining hits:
  - `base64`
  - `data:image`
  - `screenshot`
  - `payload_ref`
  - `step_ref`
  - `include_display`
- Add or update regression tests for any discovered active gap.

## Risks

- Provider adapters may intentionally convert blob/image references into data URLs at the final API boundary; this should not be mistaken for a history/context leak.
- Tests may currently assert legacy behavior around inline images; changing those tests requires confirming whether the path is provider boundary or Cortex history boundary.
- Context projection spans Cortex and agent-runtime repos, so a fix in only one layer may appear correct locally while another layer still reinjects data.

## Assumptions

- Blob/image bytes may exist inside provider-native request construction, but not as plain text tool history.
- Shell output should behave like a human terminal transcript: bounded text plus references, never opaque binary/base64 blobs.
- Cortex payload files and APIs are the source of truth for full large outputs.
- Historical display results should be recoverable by pointer/manifest, not automatically reloaded as visual context.
