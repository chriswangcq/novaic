# Phase 5D.1 Static Residue Audit And Classification

## Problem Definition

Run and record the final broad static residue audit. Remaining matches must be classified so we can distinguish current defects from historical docs, negative guards, test-only internals, migration internals, and low-level projection internals.

## Proposed Solution

- Run broad stale-term searches across `docs/cortex`, `docs/architecture`, `novaic-cortex`, and `novaic-agent-runtime`.
- Run a focused current-contract negative gate over current Cortex contract docs.
- Run a file-walk/active-path stress search.
- Classify all remaining broad hits.
- If a current unclassified defect appears, make a small correction if safe, otherwise record the defect as a known gap for the check loop.

## Acceptance Criteria

- Broad static search commands and outputs are recorded.
- Current contract negative gate is clean or any match is fixed.
- File-walk/active-path stress search is classified.
- Remaining broad hits have an explicit classification table.

## Verification Plan

```bash
rg -n "scope_state_log|register_scope_id|get_scope_id_index|meta\\.scope_ids|_walk_scope_tree|format_for_llm|include_display|_SKILL_LOCKS|_SCOPE_LOCKS|novaic-cortex-sandbox-|fallback authority|local authority|Single-process service|in-memory caching" docs/cortex docs/architecture novaic-cortex novaic-agent-runtime -S
rg -n "_SKILL_LOCKS|asyncio\\.Lock|_SCOPE_LOCKS|_walk_scope_tree|include_display|format_for_llm|scope_state_log" docs/cortex/builtin-tools-and-skills.md docs/cortex/invariants.md docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S
rg -n "resolve_active_scope_path|file-walk|file walk|文件遍历|walk.*scope|scope.*walk|active path.*authority|active_path.*authority|_collect_active_stack" docs/cortex novaic-cortex/novaic_cortex -S
```

## Risks

- The broad search intentionally finds historical and negative guard text; the result must classify rather than simply count matches.

## Assumptions

- This ticket may fix small documentation residues discovered by the audit, but does not run behavior tests.
