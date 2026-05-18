# PR-184 — Runtime Queue Client compatibility cleanup

Status: `[closed]` — 2026-05-03

## Goal

Keep Runtime queue client API names aligned with the current queue service contract. Remove uncalled old aliases so Runtime does not expose two names for one operation.

## Current-State Analysis

`SagaClient.get()` is the current status read API. `SagaClient.get_saga()` is a no-op compatibility alias and has no active caller.

## Small Tickets

- [PR-184A](PR-184A-remove-sagaclient-get-saga-alias.md) — remove the old `get_saga` alias.

## Tests

- Runtime focused client contract tests.
- Full Runtime suite.

## Deployment / Git

- Deploy Runtime if active Runtime code changes.
- Commit/push `novaic-agent-runtime` and root docs/submodule pointer.

## Closure

- Closed by PR-184A.
- Runtime deployed and Queue health smoke verified.
