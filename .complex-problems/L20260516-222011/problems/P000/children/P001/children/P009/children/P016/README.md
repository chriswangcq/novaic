# Ephemeral path and media payload leakage scan

## Problem

Search for active code paths that leak ephemeral `/tmp/novaic-cortex-sandbox-*` backing paths, base64 screenshots/media as text, or generic image injection into LLM context.

## Success Criteria

- Active code/tests are searched for ephemeral path, base64/image leakage, screenshot payload, and projection keywords.
- Hits are triaged into current guard, benign test fixture, or active issue.
- Any active leakage path is fixed or routed to the relevant specialized child problem.
- Targeted tests protect the intended pointer/blob/display contract.
