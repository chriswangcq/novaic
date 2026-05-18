# Child Problem: app and monitor test fixtures

## Problem

Frontend monitor tests still include direct-tool historical records. These should be explicit legacy-history examples, while current-path monitor tests should prefer shell/agentctl examples.

## Success Criteria

- ActivityTimeline tests distinguish shell-first current behavior from legacy archived direct-tool behavior.
- Visible assertions avoid normalizing direct-tool names as active behavior.
- Focused frontend tests pass.
