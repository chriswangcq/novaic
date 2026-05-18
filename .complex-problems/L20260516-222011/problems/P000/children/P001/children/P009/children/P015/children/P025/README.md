# Follow-up: Clean ActivityTimeline legacy direct-tool assumptions

## Problem
`novaic-app/src/components/Visual/ActivityTimeline.tsx` and adjacent tests still use retired direct tool names (`im_read`, `im_reply`, `chat_reply`) as normal public-title and bookkeeping logic. That keeps old harness assumptions in a current UI path after the shell-first contract cutover.

## Success Criteria
- ActivityTimeline current-path tests use shell/agentctl-style records for message read/reply behavior.
- Any remaining old direct tool names in ActivityTimeline code are isolated in an explicitly named legacy-normalization helper or removed.
- Public behavior remains: user sees “读取了你的消息”, “已回复你”, and no raw low-level tool names.
- Focused tests for ActivityTimeline pass.

## Verification Plan
- Patch the component and tests narrowly.
- Run focused frontend tests for ActivityTimeline.
- Run focused grep over the component/tests to ensure old names only remain in explicitly legacy contexts if unavoidable.
