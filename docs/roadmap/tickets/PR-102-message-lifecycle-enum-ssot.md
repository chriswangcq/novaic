# PR-102 — Message lifecycle enum SSOT guardrails

> Historical ticket archive: this ticket predates the Environment notification
> cutover. `message_lifecycle.json` and `chat_messages.lifecycle` are no longer
> current architecture; chat message type shape now lives in
> `novaic-common/common/contracts/chat_message.json`, and Agent-loop lifecycle
> lives in Environment notifications.

| Field | Value |
| --- | --- |
| **Ticket** | PR-102 |
| **Status** | `[✓]` |
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

- [x] Add or identify canonical enum contract.
- [x] Add backend drift tests.
- [x] Add App guard test or generated snapshot comparison.
- [x] Run targeted tests.
- [x] Deploy only if active code changes require it.
- [x] Commit, push, and bump parent repo.

## Historical Implementation Notes

- At the time of this ticket, the canonical contract lived in
  `novaic-common/common/contracts/message_lifecycle.json`.
- PR-229 superseded this shape: Business `MESSAGES_DEF` no longer carries
  chat-message lifecycle columns, and App no longer exports
  `MESSAGE_LIFECYCLE_STATES`.
- `scripts/ci/lint_lifecycle.sh` now narrowly allowlists the two audited one-shot lifecycle migrations instead of failing on historical SQL that snapshots rows and writes audit entries.

## Verification

- `cd novaic-common && python -m pytest tests/test_message_lifecycle_contract.py tests/test_execution_log_display_contract.py`
- `cd novaic-business && python -m pytest tests/test_pr102_message_lifecycle_contract.py tests/test_pr100_app_entity_schema_contract.py`
- `cd Entangled/packages/server-python && python -m pytest tests/test_pr102_message_lifecycle_contract.py tests/test_message_state.py`
- `cd novaic-app && npm run test:unit -- src/types/messageContract.test.ts src/data/entities/entangledEntityContracts.test.ts`
- `cd novaic-app && npm run build`
- `scripts/ci/lint_lifecycle.sh`

## Deployment Checklist

- [x] Business deploy required because `business/schema_push.py` now imports the shared contract.
- [x] Frontend deploy required because App message constants and hidden-message filtering changed.
- [x] Parent repo bumped after child repo commits.

## Production Smoke

- `./deploy business` restarted all backends successfully.
- `./deploy frontend 0.3.0` published `https://relay.gradievo.com/resource/frontend/v0.3.0/`.
- `./deploy status` showed Entangled, Gateway, Business, Device, Queue, Blob Service, Cortex, workers, and Relay running.
- Remote import smoke on `api.gradievo.com` confirmed lifecycle states loaded from Common, Business outbox mapping matches the contract, and `INTERRUPT` is a hidden message type.
