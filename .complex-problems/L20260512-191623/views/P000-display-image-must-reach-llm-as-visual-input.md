# P000: Display image must reach LLM as visual input

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The current production investigation showed an old LLM request where a successful `display` tool result appeared in the Factory request body as `{"_mcp_content":[{"type":"text","text":"OK"}]}` and no provider-native image message was sent. Even if the currently deployed Cortex endpoint can now format that same step as image content, the system still lacks a hard end-to-end guard that prevents current-round `display` output from silently degrading into `OK` or text-only content.

Fix the runtime/Cortex/Factory boundary so current-round `display` image output either becomes provider-native visual input in the LLM request or fails loudly with diagnosable evidence. The fix must also prove that a following `system` message does not suppress image injection.

## Success Criteria
- Current-round `display` step content containing image `_mcp_content` is converted into a provider-native image message before Factory transport.
- A following `system` message after the display tool result does not prevent image injection.
- `display_perception` projection must not silently return text-only `OK` for display steps that have media payloads.
- Factory log/request snapshot should make image delivery inspectable without dumping raw base64 into the UI.
- Tests cover the full Runtime preparation path, not only isolated helper functions.
- Old or misleading fallback behavior is removed or guarded where it could hide this bug.

## Subproblems
- P001: Runtime must inject display images through full LLM preparation
- P002: Factory logs must show image delivery without raw base64
- P003: Cortex display projection must not hide missing media as OK

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R003: problems/P000/results/R003.md
- Check C003: problems/P000/checks/C003.md

## Follow-ups
- none
