# End-to-end display screenshot regression

## Problem

Create or verify an end-to-end regression path that represents the real user flow: shell/device screenshot creates a blob artifact, display perceives it, and the next LLM request receives the image while the tool result remains placeholder-only.

## Success Criteria

- Build or identify a focused regression test covering shell artifact -> display tool -> next context assembly.
- Assert provider-visible image/media input exists.
- Assert display tool result content is placeholder-only, with no raw base64 or large JSON payload.
- Assert active-stack injection after the display result does not break image attachment.
