# PR-119 — Active Code Zombie Path Audit and First Cleanup Batch

| Field | Value |
| --- | --- |
| Status | `[✓]` |
| Owner | Codex |
| Created | 2026-04-30 |
| Repos | parent docs plus affected subrepos |
| Depends on | PR-114..PR-118 |

## 目标

清理活代码里的旧分支、兼容分支和假 fallback，降低维护熵。测试 guardrail 和历史文档不作为删除目标；它们只用于证明旧路径不会回流。

## Detailed Plan

1. [x] Build a full-repo zombie-path map.
   - Search active code for `legacy`, `deprecated`, `fallback`, `compat`, `old path`, `wake summary`, `historical_summary`, `handoff_notes`, `subagent_rest`, `unread`, `read` and similar markers.
   - Exclude `.git`, caches, build output, dependency directories, and historical docs from deletion decisions.
2. [x] Classify each active-code hit.
   - Delete now: confirmed dead branch, unused wrapper, or compatibility route.
   - Keep with guardrail: explicit regression test or migration note.
   - Follow-up ticket: real behavior but too risky for this batch.
   - First delete-now batch: obsolete external result CLI flags, parent dev script callers, and Gateway's unused legacy `gateway/api/schemas.py` module.
   - Kept for later tickets: auth fallbacks, device binding legacy-list normalization, and real database migration guardrails.
3. [x] Physically delete the first low-risk confirmed old-path batch.
4. [x] Add or update invariant tests for every deleted path.
5. [x] Run unit tests and smoke tests for every affected repo.
6. [x] Deploy affected services/apps and verify remote state.
7. [x] Commit and push affected subrepos plus parent docs/submodule updates.

## Tests

- [x] Targeted tests for each affected module.
- [x] Full test suite for each affected backend repo.
- [x] App build/test if app code is touched.
  - Not applicable; no app source touched.
- [x] Static search proves deleted active paths are gone.

## Smoke / Deploy

- [x] Deploy affected backend services/apps.
- [x] Remote source assertions prove old branches are absent.
- [x] `./deploy status` shows all backend services healthy when backend services are touched.

## Git

- [x] Affected subrepo commits.
- [x] Parent docs/submodule commit.
- [x] Push all changed repos.
