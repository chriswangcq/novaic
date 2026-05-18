# PR-175 — Agent Perception Document Decision Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | docs |
| Depends on | PR-169, PR-170, PR-171, PR-173 |
| Theme | Architecture documentation correctness |

## Goal

Replace stale "pending decision" wording in the main Agent Perception-Action document with the actual implemented decisions and remaining future enhancements.

## Current-State Analysis

The main design doc still asks whether notification-only prompt, processed lifecycle, Activity Timeline source, and payload tool set are decided. Most of these are already implemented.

## Implementation

- Convert "待决策问题" into "已决策" plus "后续增强".
- Mark `im_history` / `im_search` / `im_context` according to PR-173 outcome.
- Keep the single main path explicit: Environment notification → tool observation → Cortex trace → Activity Timeline → `skill_end`.

## Tests / Smoke

- Static grep confirms no stale "第一版是否..." undecided wording remains.

## Closure

- Main Agent Perception-Action doc now uses `已决策点` and `后续增强`.
- Topic index docs were aligned to the current Environment IM and Activity Timeline boundaries.

## Deploy / GitHub

- No service deploy required.
- Commit docs in the parent repo.
