# PR-229 — Chat Message Lifecycle Shape Removal

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Message projection cleanup |
| Created | 2026-05-05 |
| Scope | Business/App/Common chat message projection contracts |
| Dependencies | PR-168E, PR-225 |

## Goal

Remove retired Agent-loop lifecycle shape from the App-facing `messages`
projection. Environment notifications own Agent processing lifecycle; chat
messages should be UI projection and delivery status only.

## Small Tickets

### PR-229A — Remove Business Schema Lifecycle Columns

- Objective: drop `lifecycle`, `claimed_by_scope`, and
  `lifecycle_updated_at` from Business `messages` schema definition.
- Scope: `novaic-business/business/schema_push.py`.
- Expected result: Business no longer pushes retired Agent-loop lifecycle shape.
- Verification: Business schema tests / targeted `rg`.

### PR-229B — Remove Common/App Lifecycle Contract Surface

- Objective: delete message lifecycle contract exports from Common/App surfaces
  that exist only for retired Agent-loop state.
- Scope: Common contract file and App message contract/types/tests.
- Expected result: App message types carry delivery status only, not Agent-loop
  lifecycle.
- Verification: App type/unit tests and targeted `rg`.

### PR-229C — Update Tests and Guards

- Objective: align Environment/message tests with the projection-only model.
- Scope: Business/App tests that mention old message lifecycle fields.
- Expected result: tests assert lifecycle is absent from notifications and no
  longer required on messages.
- Verification: focused Business/App tests.

## Acceptance

- No active `messages` entity schema contains retired lifecycle columns.
- `MESSAGE_LIFECYCLE_STATES` is gone from App runtime type surface.
- Environment notification lifecycle remains intact and separately tested.

## Closure

Closed 2026-05-05. Business `messages` schema, Common chat-message contract,
and App message entity/type contracts no longer expose retired Agent-loop
lifecycle fields. Environment notification lifecycle remains the separate wake
state owner.
