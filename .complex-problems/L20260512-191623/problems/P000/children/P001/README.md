# Runtime must inject display images through full LLM preparation

## Problem

The Runtime helper tests prove isolated `process_multimodal_messages` behavior, but the bug class occurs across the full LLM preparation path: step-ref expansion, sanitization, multimodal conversion, and message ordering. Add a full-path guard so current-round `display` images become provider-native image messages even when a `system` message follows.

## Success Criteria

- A test starts from messages containing a display `step_ref` and fake Cortex bridge output with image `_mcp_content`.
- The test runs `prepare_llm_call`, not only `process_multimodal_messages`.
- The final messages contain `assistant`, text-only `tool`, inserted `user(image_url)`, then following `system`.
- The text-only tool receipt has a placeholder and no raw image base64.
