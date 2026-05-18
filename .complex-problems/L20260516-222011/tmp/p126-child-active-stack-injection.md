# Active skill stack injection map

## Problem

Active skill stack instructions are injected into LLM context as system messages. This late injection can affect message ordering and current-round media behavior, so its source and timing must be mapped separately.

## Success Criteria

- The active stack injection source is identified and mapped from projected stack state to final LLM messages.
- Ordering relative to tool results, display results, and provider media projection is documented.
- Tests or fixtures prove active stack injection does not cause current-round display media to be treated as historical text-only output.
- Any duplicate or stale stack-injection path is removed or split into a cleanup follow-up.
