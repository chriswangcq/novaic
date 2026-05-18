# Active stack and current display media regression coverage

## Problem

Current-round display media must remain eligible for display perception even when active stack system messages are appended after tool results. The specific regression risk is that a late system message causes the display tool result to be treated as historical text-only output.

## Success Criteria

- Create or identify a focused test where a current display tool result is followed by active stack injection.
- Prove display/media projection still emits the correct current display perception content.
- Prove historical display results remain manifest/text-only and do not leak raw media.
- Fix any failure or split the failing layer into a smaller child problem.
