# Round 005 Gate Criteria

## Gate A - Gap Closure
- Desktop report must be complete and replayable.
- Tools/Desktop split wiring gap must be fixed with code commit evidence.

## Gate B - Split Operability
- At least 3 split repos pass repo-root startup/health checks.
- Evidence must be replayable by non-authors.

## Gate C - Integration
- At least 1 split end-to-end chain per team is replayed with PASS markers.
- No direct monorepo-only runtime path in migrated code paths.

## Gate D - Evidence Quality
- Reports use canonical repo URLs and include commit SHA and migrated paths.
- Incomplete items include blocker owner and `target_round`.

## Fail Conditions
- Desktop report remains template/partial
- Tauri tools startup still resolves to monorepo path
- DONE without canonical repo URL or commit SHA
