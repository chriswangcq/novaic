# PR-167 — Environment Dedicated Domain Store

> Historical ticket archive: this closed ticket predates the PR-229 chat
> projection cleanup. `chat_messages.lifecycle` and `message_lifecycle.json`
> references here are archaeology, not current architecture.

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-business`, docs |
| Depends on | PR-166 |
| Theme | Environment domain completion |

## Goal

Turn Environment from a vocabulary wrapper over `messages` into a real Business-owned domain store for event envelopes, IM messages, notifications, sender/channel/thread identity, and resource refs.

## Current-State Analysis

1. Common already defines Environment ownership, event kinds, sender kinds, notification states, transition rules, and resource ref policy in `common/contracts/environment.json`.
2. Business has `EnvironmentRepository` and `EnvironmentService`, but `PR-162B` deliberately wraps the existing `messages` entity as the first persistence substrate.
3. Hot path works, but Environment is not yet an independent event universe: there are no dedicated Entangled entities for `environment-events`, `environment-im-messages`, `environment-notifications`, or `environment-resource-refs`.
4. This keeps `chat_messages.lifecycle` and Environment notification lifecycle entangled. It is acceptable during transition, but not the final boundary.

## Small Tickets

- [x] [PR-167A — Dedicated Environment entity schema and contract guardrails](PR-167A-environment-entity-schema-contracts.md).
- [x] [PR-167B — Repository write/read path for dedicated Environment entities](PR-167B-environment-dedicated-repository.md).
- [x] [PR-167C — Environment service generic event API and lifecycle state machine](PR-167C-environment-domain-service-state-machine.md).
- [x] [PR-167D — Data migration/backfill and old message-backed repository removal](PR-167D-environment-backfill-remove-message-backed-repo.md).

## Required Flow

For each small ticket:

1. Analyze current state for that slice.
2. Implement with unit tests.
3. Run focused and relevant full tests.
4. Deploy affected services when live behavior or schema changes.
5. Commit and push child repos plus parent submodule/doc bump.

## Done Criteria

- [x] Environment has dedicated persisted entities.
- [x] Environment notifications no longer depend on `chat_messages.lifecycle` in `EnvironmentRepository`.
- [x] Resource refs are stored as refs only; raw payload is rejected by contract and tests.
- [x] Existing IM behavior is preserved during cutover.
- [x] Old message-backed repository reads are physically removed and guarded.
