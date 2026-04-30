# PR-118 — Remove Deprecated Business `subagent_context` Path

| Field | Value |
| --- | --- |
| Status | `[ ]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | `novaic-business`, `novaic-cortex` if needed, parent docs |
| Depends on | PR-67, PR-70, PR-113 |

## 旧分支

Business still has deprecated `subagent_context` wrappers and docs, while Cortex is now the source of truth for scope context and summaries.

## Detailed Plan

1. Audit active call sites for:
   - `append_subagent_context`
   - `context_append`
   - `context_get_history`
   - `/history` paths backed by old subagent context
2. Remove or reroute any surviving caller to Cortex APIs.
3. Delete deprecated wrappers once no caller remains.
4. Add guardrail preventing Business active code from referencing `subagent_context`.

## Tests

- [ ] Business internal subagent tests updated.
- [ ] Cortex scope/context tests unaffected.
- [ ] `python -m pytest`
- [ ] `python -m compileall -q business`

## Smoke / Deploy

- [ ] Agent conversation smoke still uses Cortex scope tree.
- [ ] `rg "subagent_context|append_subagent_context|context_get_history" business tests`.
- [ ] Deploy affected services.

## Git

- [ ] Business/Cortex commits as affected.
- [ ] Parent docs/submodule commit.
- [ ] Push all changed repos.

