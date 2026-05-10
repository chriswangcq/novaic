# Phase 5D.1 Static Residue Audit And Classification Result

## Summary

Ran the broad static residue audit and fixed one additional live runtime comment residue in `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`. After the fix, current live/runtime and current contract surfaces no longer contain unclassified `_SKILL_LOCKS`, `_SCOPE_LOCKS`, `_walk_scope_tree`, `scope_state_log`, `format_for_llm`, or public-step `include_display` residues.

## Done

- Ran broad residue search across `docs/cortex`, `docs/architecture`, `novaic-cortex`, and `novaic-agent-runtime`.
- Found and fixed a current live-source comment in `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` that still referenced per-root `_SKILL_LOCKS`.
- Reran broad and focused searches after the fix.
- Classified remaining hits.

## Verification

- Broad search after fix:
  - `rg -n "scope_state_log|register_scope_id|get_scope_id_index|meta\\.scope_ids|_walk_scope_tree|format_for_llm|include_display|_SKILL_LOCKS|_SCOPE_LOCKS|novaic-cortex-sandbox-|fallback authority|local authority|Single-process service|in-memory caching" docs/cortex docs/architecture novaic-cortex novaic-agent-runtime -S`
- Current live/runtime narrow search after fix:
  - `rg -n "_SKILL_LOCKS|_SCOPE_LOCKS|_walk_scope_tree|scope_state_log|format_for_llm|include_display" novaic-agent-runtime/task_queue novaic-cortex/novaic_cortex docs/cortex/builtin-tools-and-skills.md docs/cortex/invariants.md docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S`
  - returned only `include_display` in `novaic-cortex/novaic_cortex/step_result_projection.py`.
- `python3 -m py_compile novaic-agent-runtime/task_queue/utils/cortex_bridge.py` passed.

## Remaining Hit Classification

| Match Category | Files | Classification |
| --- | --- | --- |
| `_SKILL_LOCKS` in `docs/cortex/hardening-checklist.md` | historical checklist | Allowed historical material; file has historical checklist banner. |
| `_SKILL_LOCKS`, `_walk_scope_tree`, `asyncio.Lock` in `docs/cortex/architecture-review-2026-04-17.md` | historical review | Allowed dated review evidence. |
| `novaic-cortex-sandbox-*` in `sandbox.py`, `sandbox-shell.md`, and related test schema assertions | stable-path negative guard | Intentional: commands using backing paths are rejected and tests assert the warning text. |
| `fallback authority` / temp backing-path patterns in `state-authority-implementation-plan.md` | negative design guard | Intentional forbidden-pattern list. |
| `include_display` in `step_result_projection.py` and `test_resolve_for_llm.py` | low-level resolver internals | Not the public `/v1/steps/read_formatted` contract; public API uses `projection`. |
| file-walk / active-path stress hits | historical docs, design-plan negative items, or archive/debug projection wording | No current runtime file-walk authority remains advertised. |

## Known Gaps

- None for P061. Remaining hits are classified as historical, negative guard, test assertion, or low-level projection internals.

## Artifacts

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- Static audit outputs summarized above.
