# Historical image replay guardrail discovery

## Problem

Discover whether prior display/image tool outputs are replayed into later LLM requests as text-only manifest/history content rather than provider image content or raw base64, except when current-round display projection explicitly loads an image.

## Success Criteria

- History replay guardrail tests are identified with file pointers.
- Current-round display projection is distinguished from historical replay behavior.
- Any missing test or active replay violation is listed as a remediation candidate.
