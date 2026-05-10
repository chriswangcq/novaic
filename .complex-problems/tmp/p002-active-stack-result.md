# Event Backed Active Stack Status Plan

## Summary

Replace runtime active-stack walking over `steps/_index.jsonl` and `meta.json` with a SQLite operational state model. Workspace files remain a trace/export layer.

## Done

- Proposed SQLite schema:
  - `scope_events(id, root_scope_id, scope_id, parent_scope_id, event_type, generation, reason, payload_json, occurred_at, idempotency_key)`.
  - `scope_projection(root_scope_id, scope_id, parent_scope_id, phase, stack_depth, generation, skill_name, task, opened_at, closed_at, close_reason)`.
  - `active_stack_projection(root_scope_id, top_scope_id, remaining_stack_json, generation, updated_at)`.
- Write path:
  - `skill_begin` appends `ScopeOpened` and updates projections in one SQLite transaction.
  - `skill_end` appends `ScopeClosed` with reason/report/generation and updates top.
  - `finalize` appends `WakeFinalized` with `remaining_stack`, then archives/marks scopes explicitly.
  - Workspace files are written after SQLite commit as materialized trace. If trace write fails, retry from outbox.
- Read path:
  - `context/status`, active skill stack injection, and close validation read SQLite projection.
  - Context assembly can still read ContextEvent stream, but control stack comes from the operational projection.
- Migration:
  - Phase A: implement projection side-by-side and shadow-compare with `_collect_active_stack`.
  - Phase B: switch reads to SQLite projection.
  - Phase C: remove `_collect_active_stack` projection walking from runtime; keep only a repair/import CLI if needed.
- Cleanup:
  - Remove or demote active stack traversal over `steps/_index.jsonl`.
  - Keep Workspace `meta.json` and `steps/_index.jsonl` as trace artifacts, not active runtime truth.
- Tests:
  - Skill begin/end nesting.
  - Closing wrong scope rejected.
  - Finalize with open child scopes records `remaining_stack`.
  - Restart recovers top stack from SQLite.
  - Workspace trace write failure does not corrupt active projection.
  - Shadow mode catches old/new divergence before cutover.

## Verification

- Covers every `_collect_active_stack` responsibility: top scope, nesting, archived stop condition, skill names, close validation.
- Gives an explicit old-code deletion point.

## Known Gaps

- Needs implementation and migration tickets.

## Artifacts

- `.complex-problems/tmp/p002-active-stack-result.md`

