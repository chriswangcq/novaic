# PR-100 — Entangled schema and App type guardrails

| Field | Value |
| --- | --- |
| **Ticket** | PR-100 |
| **Status** | `[ ]` |
| **Scope** | `novaic-business`, `novaic-app` |
| **Depends on** | PR-99 |
| **Invariant** | App entity assumptions must match Business-pushed Entangled entity schemas. |

## Problem

Business defines Entangled entities in `schema_push.py`; App keeps entity metadata and TypeScript types separately. Field drift can be masked by permissive frontend code.

## Goal

- Add a schema snapshot/contract for key entities used by App: `messages`, `execution-logs`, and `log-payloads`.
- Add tests that compare App entity metadata against the backend schema contract.
- Make future field additions explicit.

## Non-Goals

- Do not build a full schema generator unless the guardrail proves insufficient.
- Do not migrate stored Entangled data.
- Do not change entity names or table names.

## Checklist

- [ ] Export or snapshot key Business entity schema metadata.
- [ ] Add App-side drift tests for entity names/id fields/key fields.
- [ ] Run Business/App tests.
- [ ] Deploy if runtime code changes require it.
- [ ] Commit, push, and bump parent repo.

