# PR-146 — Documentation and Runbook Archaeology Residue Scan

| Field | Value |
| --- | --- |
| Status | `[scanned]` |
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

## Follow-up Decision

Rewrite current docs first, archive historical roadmaps explicitly, and add docs lint for retired terms only after the remaining valid historical references are isolated.

## Unit / Guardrail Tests

- [ ] Add docs lint only after current docs are rewritten and historical docs have explicit archive banners.

## Smoke / Deploy

- [x] No deploy for docs scan.

## Git / Merge

- [ ] Commit ticket updates.
- [ ] Push parent docs update.
