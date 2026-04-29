# PR-102 — Message lifecycle enum SSOT guardrails

| Field | Value |
| --- | --- |
| **Ticket** | PR-102 |
| **Status** | `[ ]` |
| **Scope** | `novaic-common`, `Entangled`, `novaic-business`, `novaic-app` |
| **Depends on** | PR-101 |
| **Invariant** | Message types and lifecycle states must be known consistently across producer, state machine, and UI. |

## Problem

Message kinds (`USER_MESSAGE`, `AGENT_REPLY`) and lifecycle states are referenced across Common, Business, Entangled, Runtime, and App. Adding or renaming one can create silent fallback behavior.

## Goal

- Identify canonical enum source(s) for message type and lifecycle.
- Add drift tests across backend and App-facing constants.
- Prevent lifecycle/state additions without explicit UI/backend review.

## Non-Goals

- Do not rewrite the Entangled state machine.
- Do not migrate historical messages.
- Do not change current message lifecycle behavior.

## Checklist

- [ ] Add or identify canonical enum contract.
- [ ] Add backend drift tests.
- [ ] Add App guard test or generated snapshot comparison.
- [ ] Run targeted tests.
- [ ] Deploy only if active code changes require it.
- [ ] Commit, push, and bump parent repo.

