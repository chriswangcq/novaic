# PR-166A — Activity Timeline Projection Contract

> Historical note: superseded by PR-193. The old Cortex `/v1/trace/project` HTTP contract has been removed; current Agent Monitor rows are Entangled projection entities.

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-166 |
| Repos | `novaic-cortex`, docs |

## Goal

Make Cortex `/v1/trace/project` return a user-facing Activity Timeline projection, not a mixed debug trace.

## Current-State Analysis

Cortex already projects observation / reasoning / action / summary phases, but the current record shape still exposes debug-oriented fields:

- `source`
- `tool_call_id`
- `arguments_preview`
- `payload_ref`

Those fields are useful for implementation debugging, but they should not be the default contract for the Agent Monitor. The monitor needs product-level records: what the agent noticed, how it reasoned, what it did, what happened, and whether there is more payload behind the scenes.

## Implementation Plan

1. Define the public record shape in code/tests:
   - `order`
   - `phase`
   - `kind`
   - `title`
   - `text`
   - `truncated`
   - optional `tool`
   - optional `status`
   - optional `has_payload`
2. Remove debug fields from the default projection: `source`, `tool_call_id`, `arguments_preview`, `payload_ref`.
3. Convert tool-call arguments into product-level action text where useful, with conservative redaction for secret-like keys.
4. Make tool observations use stored observation `preview` / `summary`; do not fall back to raw tool result as default user-facing text.
5. Add tests that fail if raw payloads or debug ids leak into projected records.

## Unit / Guardrail Tests

- [x] Cortex projection separates observation / reasoning / action / summary.
- [x] Action text is product-level and does not expose raw JSON argument previews.
- [x] Observation exposes `has_payload` instead of raw `payload_ref`.
- [x] Projection records do not include debug fields.
- [x] Closed scope projects only `summary.md`.

## Smoke / Deploy / Git

- [x] Run focused Cortex projection tests.
- [x] Run full Cortex tests.
- [x] Deploy Cortex service.
- [x] Remote source smoke.
- [ ] Commit Cortex and parent docs/submodule pointer.

## Evidence

```bash
cd novaic-cortex && PYTHONPATH=.:../novaic-common pytest -q tests/test_trace_projection.py
# 6 passed

cd novaic-cortex && PYTHONPATH=.:../novaic-common pytest -q
# 397 passed, 16 skipped

./deploy cortex
# Cortex deployed; all backend services restarted

./deploy status
# ports 19900/19999/19998/19993/19997/19995/19996 healthy; relay active
```

Remote source smoke:

```text
PUBLIC_RECORD_FIELDS = ['has_payload', 'kind', 'order', 'phase', 'status', 'text', 'title', 'tool', 'truncated']
No default projection source tokens: arguments_preview, payload_ref, tool_call_id, source, scope_path
```

Remote Cortex venv does not include pytest, so production smoke used source-contract inspection after deploy rather than running the test suite in-place.

## Acceptance Criteria

- [x] Activity Timeline projection is safe to hand to a normal Agent Monitor.
- [x] Developer-only join ids / payload refs are not part of the default projected record shape.
- [x] Reasoning still comes directly from provider `reasoning_content`; no extra monitor-only summary is introduced.
