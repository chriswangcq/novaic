# Business dispatch active residue scan and safe cleanup

## Problem

The business dispatch adapter code needs a focused active-path scan for fallback/compatibility/migration/TODO/direct-tool residue. The scan must classify every hit and only apply safe cleanup that does not change queue/FSM dispatch behavior.

## Success Criteria

- Scan `novaic-business` active implementation and relevant focused tests for `legacy`, `fallback`, `compat`, `migration`, `TODO`, `FIXME`, and direct tool terms such as `im_read`, `im_reply`, `payload_read`, `audio_qa`, and `subagent_spawn`.
- Inspect each non-obvious hit and classify it as active-risk, safe cleanup, guard/test-only, or unrelated domain terminology.
- Apply safe comment/dead-code cleanup directly where it removes misleading residue without behavior changes.
- Run focused business tests for touched files, or explicitly record any unavailable test path.
- Produce a result that maps changes and classifications back to this checklist.
