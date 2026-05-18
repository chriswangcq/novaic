# Cortex projection and payload large-output sweep

## Problem
Audit Cortex step projection, payload APIs, and context assembly for large-output boundaries, including unknown dict fallback, payload read/search/summarize/qa, and history/current projection text limits.

## Success Criteria
- Cortex projection/payload clusters are cited and classified.
- Payload inspection is bounded or model-mediated with explicit limits.
- Unknown or legacy step result shapes cannot dump unbounded JSON into LLM context.
