# PR-193C — App Agent Monitor Entangled Read Path

Status: closed

## Analyze

`useActivityTimeline` currently imports `entangledMethod`, calls `agents.activity_timeline`, and runs an interval. That is a product mismatch: the App should observe local Entangled cache rows already synced by the backend.

## Small Work Orders

1. Add `agentActivityRecordsStore` and `agentActivityParticipantsStore`.
2. Rewrite `useActivityTimeline` to derive records and participants from these stores.
3. Keep public UI component props stable where possible.
4. Remove polling-related options and state.
5. Update App tests to mock stores instead of action calls.

## Tests

- Hook normalization/filter tests.
- ChatPanel monitor source guard.
- ActivityTimeline rendering tests.
- Entangled contract tests.

## Acceptance

`useActivityTimeline` has no `entangledMethod`, no `setInterval`, and no polling option. Monitor updates are driven by Entangled cache invalidation.

## Closure

Closed 2026-05-03. `useActivityTimeline` reads Entangled stores directly and derives public monitor records/participants without action polling.
