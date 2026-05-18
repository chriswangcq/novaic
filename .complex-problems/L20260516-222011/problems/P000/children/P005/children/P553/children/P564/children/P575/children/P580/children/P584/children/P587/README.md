# Child Problem: Verify display durable no-base64 and image delivery

## Problem

Run focused tests and static scans proving display durable payloads no longer store inline image bytes, while provider requests still receive current display images and history replay stays text-only.

## Success Criteria

- Focused runtime and Cortex display projection tests pass.
- Static scans do not find tests or code requiring `durable_payload.llm_content._mcp_content[].data`.
- Evidence artifacts record commands and outputs.
