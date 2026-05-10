# Scope Transition Log Replacement Plan

## Summary

Replace `scope_state_log_path` local NDJSON with SQLite-backed transition events. Treat logs as queryable observability derived from the same operational state ledger, not as separate files.

## Done

- Proposed schema:
  - Reuse `scope_events` for `ScopeOpened`, `ScopeClosed`, `ScopeArchived`, `WakeFinalized`, `RecoveryStarted`, `RecoveryCompleted`.
  - Add indexes on `(scope_id, occurred_at)` and `(root_scope_id, seq)`.
  - Optional `scope_transition_export_offsets` table if exporting to logs/metrics.
- API behavior:
  - `list_transitions(scope_path)` becomes `list_scope_events(scope_id)` backed by SQLite.
  - `append_transition(...)` disappears as a separate best-effort local file write.
  - If external logs are needed, a background exporter tails SQLite and writes to logs; exporter failure never changes canonical state.
- Configuration cleanup:
  - Remove required `--scope-state-log-path` from Cortex startup after migration.
  - Delete code paths that normalize local log paths.
  - Keep a one-time import tool only if old deployments need migration; user has said old data can be deleted in previous context, so default plan is no backward migration.
- Tests:
  - Transition history query returns lifecycle events.
  - Exporter failure does not fail skill_end.
  - Restart preserves history.
  - Startup no longer requires local log path.

## Verification

- Removes persistent local file as a state plane.
- Preserves replay/debug through SQLite events.

## Known Gaps

- Needs implementation after the SQLite operational ledger exists.

## Artifacts

- `.complex-problems/tmp/p003-scope-log-result.md`

