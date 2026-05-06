# PR-257 Reliable Evolution FSM-10 Remove Active Sessions Table

Status: `[x]` closed

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
- Add a schema migration that drops existing `tq_active_sessions`.
- Remove all runtime writes/deletes to `tq_active_sessions`.
- Update readiness checks to validate `tq_session_state` instead.
- Rewrite tests that still seed/query the old table.
- Add residue guard that fails if runtime source references the retired table.

## Out Of Scope

- Do not change the public `/api/queue/sessions/active` diagnostics contract;
  it should keep projecting from `tq_session_state`.
- Do not alter inbox/outbox/finalize behavior.

## Small Tickets

- [x] **FSM-10-A Schema removal**: bump schema and drop the table in migration.
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
- Existing production DBs need schema v14 migration to run during deployment;
  the migration is covered by `tests/test_pr257_remove_active_sessions_table.py`.

## Verification

- `pytest tests/test_pr252_session_state_ssot.py tests/test_pr245_suspected_dead_recovery.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr257_remove_active_sessions_table.py -q`
- `pytest -q`
- `git diff --check`

## Review Result

Pass. Fresh schema no longer creates `tq_active_sessions`, schema v14 drops it
from existing DBs, readiness checks use `tq_session_state`, runtime writes to
the old table are gone, and residue guards allow only the drop migration plus
tests/docs to mention the retired table name.

## Rollback

Revert PR-257. The old cache table and writes return, but routing must still be
kept on `tq_session_state`.
