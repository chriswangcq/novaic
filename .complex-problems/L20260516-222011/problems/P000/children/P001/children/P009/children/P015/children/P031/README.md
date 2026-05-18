# Follow-up: Update Cortex environment notification hint to shell-first IM read

## Problem
`novaic-cortex/novaic_cortex/context_event_projection.py` still builds active LLM notification text saying `Use im_read(notification_ids=[...])`. After the shell-first cutover, active prompts must direct the model to call `shell` with `agentctl im read ...` instead.

## Success Criteria
- Notification hint text uses shell/agentctl wording, not direct `im_read`.
- Relevant Cortex tests are updated or added.
- Focused grep confirms active context projection no longer emits direct `im_read` guidance.
- Focused tests pass.

## Verification Plan
- Inspect existing tests for notification projection/context preparation.
- Patch projection and tests narrowly.
- Run focused pytest for context projection / tool schema limits if available.
