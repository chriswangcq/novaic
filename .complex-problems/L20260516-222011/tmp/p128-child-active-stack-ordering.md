# Verify active-stack ordering does not suppress current display media

## Problem

The active skill stack/system message is appended near the end of context. Verify current display-derived media remains present and correctly ordered even when a system Active Skill Stack message follows the display tool result.

## Success Criteria

- There is a targeted test for display result followed by active-stack/system message.
- The prepared LLM messages still include a provider image user message.
- The display tool result text is sanitized with placeholders rather than base64.
