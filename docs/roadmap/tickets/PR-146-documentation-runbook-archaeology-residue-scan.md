# PR-146 — Documentation and Runbook Archaeology Residue Scan

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | parent docs plus subrepo docs |
| Depends on | PR-145 |

## Goal

Find docs that describe retired paths as if they were current. Archaeology is allowed only when clearly marked as history; operational docs and runbooks must reflect the current single path.

## Scan Plan

1. [x] Search docs for retired path names and old topology descriptions.
2. [x] Classify hits as current docs, historical tickets, or explicit archaeology.
3. [x] Identify docs that should be rewritten or deleted.
4. [x] Add doc lint candidates for high-risk old terms.

## Findings

- Safe archaeology already marked clearly enough:
  - `docs/cortex/hardening-checklist.md`
  - `docs/cortex/architecture-review-2026-04-17.md`
  - `docs/cortex-architecture.md`
  - `docs/cortex/recall.md`
- Current/stale docs that can mislead future work:
  - `docs/runtime/react-agent-loop.md` still says native `function_call` is stripped/ignored and tools are JSON in the system prompt, contradicting current native tool-call execution.
  - `docs/runtime/tool-chain-dispatch.md` uses imprecise ownership language around Cortex, Business, Device, Gateway, and CloudBridge.
  - `docs/architecture/gateway-decomposition-roadmap.md` reads historical but is not strongly archived; it still describes old Cortex/Gateway topology.
  - `docs/runbooks/subscriber-canary.md` treats subscriber canary as an operational path, conflicting with `subscriber_enabled=false`.
  - `docs/runbooks/troubleshooting.md` still includes subscriber-enabled and old `message_outbox` troubleshooting language.
  - `docs/architecture/service-topology.md` still mentions hidden Runtime Orchestrator arg behavior that should disappear when PR-140 cleanup lands.
  - `docs/architecture/agent-pipeline.md` still lists `DispatchSubscriber` as part of the architecture.
- Script residue surfaced during docs scan:
  - `scripts/check_entity_store_pk.py`
  - `scripts/sync_entity_id_fields.sh`
  - `scripts/gateway/export_entity_id_fields.py`

## Implementation

- Rewrote current Runtime docs:
  - `docs/runtime/react-agent-loop.md`
  - `docs/runtime/tool-chain-dispatch.md`
- Updated current architecture docs to remove stale codegen, Watchdog, RO CLI, and subscriber-canary wording:
  - `docs/architecture/app-ui.md`
  - `docs/architecture/attention-points.md`
  - `docs/architecture/service-topology.md`
  - `docs/architecture/agent-pipeline.md`
  - `docs/architecture/overview.md`
  - `docs/architecture/data-ownership.md`
- Replaced the old subscriber canary runbook with an archived note that points to the required subscriber process checks.
- Rewrote troubleshooting to treat subscriber as required, not switch-controlled.
- Marked the Gateway decomposition roadmap as historical.
- Updated stale roadmap wording for model entity frontend contract work.
- Added `scripts/ci/lint_current_docs_residue.sh` and wired it into CI.

## Follow-up Decision

Rewrite current docs first, archive historical roadmaps explicitly, and add docs lint for retired terms only after the remaining valid historical references are isolated.

## Unit / Guardrail Tests

- [x] Added current-docs residue lint after isolating historical docs.

## Smoke / Deploy

- [x] `./scripts/ci/lint_current_docs_residue.sh`
- [x] Current docs grep for high-risk retired terms returns no matches outside archived/history locations.

## Git / Merge

- [x] Implementation ready for commit in this batch.
- [x] Parent docs updated.
