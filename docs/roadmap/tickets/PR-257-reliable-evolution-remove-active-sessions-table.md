# PR-257 Reliable Evolution FSM-10 Remove Active Sessions Table

Status: Closed

## Goal

Physically remove `tq_active_sessions` from the runtime harness. After
PR-252..PR-255, `tq_session_state` is already the live session authority; the
remaining active-session table is now misleading residue.

## Phase Ledger

```text
Phase: FSM-10 remove active_sessions table
Subject: active session authority
Old source of truth: tq_active_sessions cache/view residue
New source of truth: tq_session_state only
Input events: unchanged append-only tq_session_events
Decision function: decide_session_dispatch from explicit SessionDispatchInput
State transition: SessionLedgerRepository.upsert_state
Outbox effects: create_wake_saga, publish_attach_input, recovery_archive_scope
Legacy deletion condition: no runtime source references tq_active_sessions
Tests: schema migration drops table; dispatch/rebuild/session_ended work from session_state
```

## Scope

- Remove `tq_active_sessions` creation from schema SQL.
- Confirm production ran the schema migration, then remove the drop migration
  residue from active schema code.
- Remove all runtime writes/deletes to `tq_active_sessions`.
- Update readiness checks to validate `tq_session_state` instead.
- Rewrite tests that still seed/query the old table.
- Add residue guard that fails if runtime source references the retired table.

## Out Of Scope

- Do not change the public `/api/queue/sessions/active` diagnostics contract;
  it should keep projecting from `tq_session_state`.
- Do not alter inbox/outbox/finalize behavior.

## Small Tickets

- [x] **FSM-10-A Schema removal**: remove schema creation and, after production
  migration completion, delete the one-shot drop migration code.
- [x] **FSM-10-B Runtime write removal**: remove cache writes/deletes in
  repository and outbox dispatcher.
- [x] **FSM-10-C Diagnostics preservation**: keep active session diagnostics
  reading from `tq_session_state`.
- [x] **FSM-10-D Test rewrite**: remove direct table seeding/assertions.
- [x] **FSM-10-E Residue guard**: assert no runtime source contains
  `tq_active_sessions`.

## Explicit Dependency Boundary Review

Verdict: target compliant.

Boundary:
- Core under review: session FSM state authority and dispatch decision inputs.
- Allowed imperative shell: schema migration, repository persistence, readiness
  checks.

Hidden inputs found:
- `tq_active_sessions` is no longer read for live routing, but its presence as
  a cache can mislead future code into reading ambient DB state outside the
  explicit `SessionDispatchInput` / `SessionStateRecord` boundary.

Required fixes:
- Remove the table and all runtime references.
- Prove dispatch/rebuild/finalize behavior depends on `tq_session_state` only.
- Add guard tests preventing old-table resurrection.

Residual risks:
- None for production after verification: `/opt/novaic/data/queue.db` is schema
  version 14 and no longer contains `tq_active_sessions`. Older private DB
  snapshots that never ran PR-257 will need manual cleanup instead of carrying
  long-lived runtime migration residue.

## Verification

- `pytest tests/test_pr252_session_state_ssot.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr257_remove_active_sessions_table.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Pass. Fresh schema no longer creates `tq_active_sessions`; production DB was
verified at schema version 14 with the old table absent; the one-shot drop
migration was then deleted from active schema code. Readiness checks use
`tq_session_state`, runtime writes to the old table are gone, and residue guards
assert active runtime source does not mention the retired table name.

## Rollback

Revert PR-257. The old cache table and writes return, but routing must still be
kept on `tq_session_state`.
