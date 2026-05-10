# Remaining legacy filesystem write audit result

## Summary

Completed the Phase 3.6 static audit. Active API context write paths are routed through projection-named methods after event append. Remaining legacy file writes are classified as transitional projection materialization, projection read support, operational metadata support, archive index maintenance, or test setup. One unused legacy overwrite method, `Workspace.write_context`, was physically deleted.

## Done

- Audited active API calls for direct generic Workspace write methods.
- Audited production references to `context.jsonl`, `steps/_index.jsonl`, `steps/*.json`, `summary.md`, and `meta.json`.
- Audited raw system write helpers in `workspace.py` and `api.py`.
- Deleted unused direct overwrite method `Workspace.write_context`.
- Confirmed no `Workspace.write_context` definition or call remains.

## Verification

- Active API generic write scan:
  - `rg -n "await ws\\.(append_context|append_context_batch|write_step|complete_child_scope|archive_root_scope|append_input_message_ids|create_scope)\\(" novaic_cortex/api.py`
  - Result: no matches.
- Projection call scan:
  - Active API calls now use `create_scope_projection`, `archive_root_scope_projection`, `complete_child_scope_projection`, `append_context_projection`, `append_context_batch_projection`, `append_input_message_ids_projection`, and `write_step_projection`.
- Legacy overwrite scan:
  - `rg -n "def write_context|\\.write_context\\(" novaic_cortex tests`
  - Result: no matches.
- Full Cortex suite:
  - `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q`
  - Result: `446 passed in 0.84s`

## Classification

- `workspace.py` scope lifecycle writes (`meta.json`, `steps/_index.jsonl`, `summary.md`, archive move/index):
  - Classified as transitional projection materialization. Active API reaches these through projection-named methods.
- `workspace.py` context writes (`append_context`, `append_context_batch`):
  - Classified as transitional context projection materialization. Active API reaches these through projection-named methods.
- `workspace.py` step writes (`write_step`, step payload/index writes):
  - Classified as transitional tool-step projection materialization. Active API reaches these through `write_step_projection`.
- `workspace.py` payload writes:
  - Classified as support/debug payload storage for bounded tool output inspection, not context source-of-truth.
- `workspace.py` `update_session_meta`, `append_input_message_ids`, `register_scope_id`:
  - Classified as operational metadata projection/support writes. Active notification attach uses `append_input_message_ids_projection`.
- `api.py` `_sys_write` in `/v1/admin/reindex_scopes`:
  - Classified as archive index maintenance/debug support, not context source-of-truth.
- Tests using raw Workspace writes:
  - Classified as setup/support for projection, rendering, payload, and legacy-reader tests.

## Known Gaps

- None requiring a P045 follow-up. Read-path cutover will later decide which projection methods/files can be deleted outright.

## Artifacts

- Changed: `novaic-cortex/novaic_cortex/workspace.py`
