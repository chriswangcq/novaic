# PR-193A — Agent Activity Entangled Entity Contracts

Status: closed

## Analyze

Current App-facing Entangled contract only exposes `messages`. Agent Monitor participants and records are fetched through the `agents.activity_timeline` action, so the App has no stream/list entity to subscribe.

## Small Work Orders

1. Add Business schemas:
   - `agent-activity-records`
   - `agent-activity-participants`
2. Add these two entities to `common/contracts/entangled_app_entities.json`.
3. Mirror the contract in App `entangledEntityContracts.ts`.
4. Subscribe both entities from the conversation route by `agent_id`.
5. Add contract tests proving the App schema matches Business.

## Tests

- Business app entity contract test.
- Common app contract guard.
- App entangled entity contract test.
- App nav subscription guard.

## Acceptance

The entities are registered by Business, visible to App contract tests, and the route subscription contains only product projection entities, not raw runtime tables.

## Closure

Closed 2026-05-03. Business, Common, App contracts, and Tauri conversation-route subscriptions all include `agent-activity-records` and `agent-activity-participants`.
