# Formatted step read and display projection ref contract

## Problem

Formatted step reads and display projection are the bridge from durable step storage into LLM-visible multimodal context. This path must use stable step lookup refs while reading actual payload content from the correct payload location, and it must not reintroduce raw media into public tool messages.

## Success Criteria

- Map `read_step_formatted`, `StepResultClient`, display projection expansion, and provider multimodal conversion around `step_ref`/`payload_ref`.
- Prove stable step lookup works even when raw media is stored in durable/external payload form.
- Prove public tool message placeholders do not contain raw image/base64 data while LLM image projection can still be constructed only for explicit display perception.
- Fix or split any broken or ambiguous formatted-read behavior.
