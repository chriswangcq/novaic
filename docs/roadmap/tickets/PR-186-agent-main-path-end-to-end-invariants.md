# PR-186 — Agent Main Path End-to-End Invariants

Status: `[closed]` — 2026-05-03

## Goal

Turn the Environment → Runtime → Cortex → Activity Timeline architecture into explicit end-to-end acceptance guards.

This ticket verifies the ten-part Environment plan after PR-162..PR-171:

1. Environment contract / domain model
2. Environment storage / repository
3. Environment domain service / state machine
4. Runtime tool executor integration
5. Cortex observation write path
6. Subscriber / Queue notification lifecycle
7. Prompt notification-only model
8. Activity Timeline projection
9. Payload interpretation tools
10. Physical deletion of old paths / guardrails

## Current-State Analysis

PR-162..PR-171 implemented the main structure:

- Environment has dedicated event/message/notification/resource-ref contracts, storage, repository, and service tests.
- Runtime exposes Environment IM tools and blocks `im_reply` until current wake notifications have been observed through `im_read`.
- Runtime prompt context receives Environment notification hints, not raw unobserved user message bodies.
- Runtime session lifecycle claims Environment notifications at `session.init` and marks them processed after successful Cortex scope archive.
- Cortex stores the work trajectory, externalizes large tool payloads, preserves provider reasoning, and projects Observation / Reasoning / Action / Summary records.
- App Agent Monitor consumes Activity Timeline as the user-facing surface and guards against raw debug fields.
- Old execution-log, `chat_reply`, `subagent_report/query/cancel`, message-lifecycle/outbox, wake-summary, and raw prompt replay paths have been deleted or guarded.

The remaining risk is not one missing feature; it is drift across module boundaries. PR-186 adds acceptance-level tests and documentation that bind those pieces together.

## Small Tickets

- [x] [PR-186A — Runtime wake observation/reply lifecycle acceptance](PR-186A-runtime-wake-observation-reply-lifecycle.md)
- [x] [PR-186B — Business Environment notification hot-path acceptance](PR-186B-business-environment-notification-hot-path.md)
- [x] [PR-186C — Cortex trace and payload invariant acceptance](PR-186C-cortex-trace-payload-invariants.md)
- [x] [PR-186D — App Agent Monitor public-surface acceptance](PR-186D-app-agent-monitor-public-surface.md)
- [x] [PR-186E — Cross-repo old-path residue guard and closure](PR-186E-cross-repo-old-path-residue-guard.md)

## Required Process

For each small ticket:

1. Analyze current implementation and tests.
2. Add or tighten the minimum acceptance tests/guards.
3. Run the relevant module tests and a smoke check.
4. Deploy if runtime behavior changed.
5. Commit and push the touched subrepo, then update the parent repo pointer/docs.
6. Only close the ticket when old-path ambiguity is removed.

## Done Criteria

- [x] A notification-triggered wake can only reason from message content after `im_read`.
- [x] Reply, tool action, reasoning, observation, payload inspection, scope close, and notification finalization each have one owner.
- [x] The LLM prompt does not contain raw unobserved user message bodies.
- [x] Cortex does not inline raw large/sensitive payloads into default prompt context.
- [x] Agent Monitor shows user-facing activity, not raw execution diagnostics.
- [x] Static guards prevent old communication, wake summary, execution-log, and raw prompt replay paths from returning.

## Closure

Closed 2026-05-03.

Validation:

- `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q` → `176 passed`
- `novaic-business`: `PYTHONPATH=. pytest -q` → `154 passed`
- `novaic-cortex`: `PYTHONPATH=. pytest -q` → `402 passed, 16 skipped`
- `novaic-app`: `npm run test:unit` → `38 passed`; `npm run build` → passed
- Root guard: `scripts/ci/lint_agent_main_path_acceptance.sh && scripts/ci/lint_retired_agent_paths.sh && scripts/ci/lint_lifecycle_loop_ownership.sh` → passed

No production deploy was required because this ticket added acceptance tests, docs, and static guards only; no runtime behavior changed.
