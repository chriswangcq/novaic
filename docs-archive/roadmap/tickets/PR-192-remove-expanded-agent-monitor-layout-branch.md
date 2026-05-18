# PR-192 Remove Expanded Agent Monitor Layout Branch

Status: closed

## Background

After the participant selector was moved to a product-facing floating Agent Monitor, `ChatPanel` still carried the old expanded Agent Monitor layout branch. That branch had no valid product entry point, but it still persisted layout state and could mislead future maintenance back toward the deleted execution-log diagnostic surface.

## Scope

- Physically remove the old expanded Agent Monitor branch from `ChatPanel`.
- Remove `logExpanded` / `logHeightRatio` layout persistence, store state, hook selectors, and config constants.
- Bump layout persistence schema so old expanded-monitor state cannot revive the deleted path.
- Add guard coverage that rejects the old branch strings and ChatPanel resizer import.

## Validation

- `npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/SubagentList.test.tsx src/components/Visual/ActivityTimeline.test.tsx src/components/hooks/useActivityTimeline.test.ts`
  - 4 files passed, 16 tests passed.
- `npm run build`
  - Passed. Existing Vite chunk warnings remain unrelated.
- Residue scan:
  - No production ChatPanel/store/config/type code keeps `logExpanded`, `logHeightRatio`, `setLogExpanded`, `setLogHeightRatio`, `resetLogHeightRatio`, `LOG_HEIGHT_RATIO`, or the old expanded Agent Monitor branch.
  - Remaining `<Resizer` references are the unrelated layout/drawer resizers plus guard-test strings.

## Closure

Closed by removing the misleading old branch instead of keeping it dormant. Agent Monitor now enters through the participant floating layer only; the old split-pane execution-log style monitor can no longer be revived by persisted layout state.
