# PR-193D — Delete Activity Timeline Action Hot Path

Status: closed

## Analyze

The old `agents.activity_timeline` action is an attractive nuisance: it hides a synchronous App-to-Business-to-Cortex query path behind an Entangled action name. It must be physically removed after the entity projection is wired.

## Small Work Orders

1. Remove `activity_timeline_action` and helper functions from Business.
2. Remove `activity_timeline` from `ENTITY_ACTIONS["agents"]`.
3. Delete or rewrite tests that assert the old action exists.
4. Add a guard that rejects `/v1/trace/project` calls from Business/App hot-path code.

## Tests

- Business schema/action guard.
- Static grep guard for `activity_timeline` action fallback.
- App guard for no action call.

## Acceptance

There is no Business action or App call that can revive the polling Cortex projection path.

## Closure

Closed 2026-05-03. Removed Business `activity_timeline_action`, removed schema registration, deleted old tests, and removed Cortex `/v1/trace/project`.
