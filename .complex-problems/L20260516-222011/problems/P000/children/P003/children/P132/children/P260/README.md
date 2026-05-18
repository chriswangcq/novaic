# Agent-runtime current versus historical media regression coverage

## Problem

Agent-runtime assembles the LLM context and decides whether display media is current-turn provider media or historical sanitized text. It needs focused tests that prove current display media survives as provider-native media while later history replay does not re-inject raw media payloads.

## Success Criteria

- Focused runtime context tests pass.
- Tests prove current explicit display perception can become provider-native image content.
- Tests prove historical display/tool messages replace image data with placeholders or manifest text.
- Tests prove shell output remains bounded terminal text and does not become display media by content sniffing.
