# PR-118 — Remove Deprecated Business `subagent_context` Path

| Field | Value |
| --- | --- |
| Status | `[✓]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-business`, `novaic-cortex` if needed, parent docs |
| Depends on | PR-67, PR-70, PR-113 |

## 旧分支

Business still has deprecated `subagent_context` wrappers and docs, while Cortex is now the source of truth for scope context and summaries.

## Detailed Plan

1. [x] Audit active call sites for:
   - `append_subagent_context`
   - `context_append`
   - `context_get_history`
   - `/history` paths backed by old subagent context
2. [x] Remove or reroute any surviving caller to Cortex APIs.
   - No active in-tree caller found; Cortex scope/context APIs are already the authoritative path.
3. [x] Delete deprecated wrappers once no caller remains.
   - Removed Business `context_append` / `context_get_history` wrappers.
   - Removed deprecated `/subagents/{agent_id}/{subagent_id}/history` and `/context/append` routes.
4. [x] Add guardrail preventing Business active code from referencing `subagent_context`.
   - Added `tests/test_pr118_subagent_context_removed.py`.

## Tests

- [x] Business internal subagent tests updated.
- [x] Cortex scope/context tests unaffected.
- [x] `python -m pytest`
- [x] `python -m compileall -q business`

## Smoke / Deploy

- [x] Agent conversation smoke still uses Cortex scope tree.
- [x] `rg "subagent_context|append_subagent_context|context_get_history" business tests`.
- [x] Deploy affected services.

## Git

- [x] Business/Cortex commits as affected.
- [x] Parent docs/submodule commit.
- [x] Push all changed repos.
