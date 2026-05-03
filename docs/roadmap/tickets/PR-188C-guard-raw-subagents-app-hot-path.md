# PR-188C — Guard Raw Subagents Out of the App Hot Path

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-app`, `novaic-common`, docs |
| Parent | PR-188 |

## Goal

Prevent raw `subagents` from being reintroduced into the normal App hot path.

## Current-State Analysis

The raw Business `subagents` table is runtime orchestration state. The App should consume monitor participants through `agents.activity_timeline` product projection instead.

## Implementation Plan

- Keep `subagents` out of `common/contracts/entangled_app_entities.json`.
- Keep `subagents` out of `APP_ENTANGLED_ENTITY_CONTRACTS`.
- Keep `subagents` out of `route_subscriptions(...)` for conversation/chat.
- Add or update guard tests that reject raw `subagentsStore` and route subscriptions.
- Keep `execution-logs` out of normal monitor subscriptions.

## Tests

- App Entangled contract tests reject `subagents` and `execution-logs`.
- ChatPanel guard rejects `subagentsStore`, `useLogs`, and `ExecutionLog`.
- Rust nav guard or source test rejects `execution-logs` and `subagents` conversation subscriptions.
- App build and Tauri check pass.

## Done Criteria

- The normal App monitor path cannot accidentally subscribe raw runtime entities.

## Closure

Closed 2026-05-03.

Implemented in `novaic-app`:

- Removed the conversation-route `execution-logs` subscription.
- Removed the raw `subagents` App hot-path attempt from the final design.
- Deleted stale `logFilterStore`, old subagent types, and old log grouping utilities.
- Added guard checks for App contracts, `ChatPanel`, and nav subscriptions.

Validation:

```bash
npm run test:unit -- src/components/hooks/useActivityTimeline.test.ts src/components/Visual/SubagentList.test.tsx src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/ActivityTimeline.guard.test.ts src/components/Visual/ActivityTimeline.test.tsx src/data/entities/entangledEntityContracts.test.ts
cargo check
rg -n "logFilterStore|SubAgentMeta|SubAgentNode|buildSubAgentTree|getLogGroupKey|isMainAgent|subagentsStore|SubSpec::new\\(\\s*\\\"subagents\\\"|SubSpec::new\\(\\s*\\\"execution-logs\\\"|\\\"subagents\\\"|execution-logs" novaic-app/src novaic-app/src-tauri/src novaic-common/common/contracts novaic-common/tests -g '!node_modules'
```
