# Phase 5C Current Docs And Comments Cleanup

## Problem

Even after code cleanup, stale comments and current docs can mislead future agents into treating in-memory locks, temp sandbox paths, BlobRefs, or file walks as authority. Current architecture documentation and live-code comments need to reflect the final state authority boundaries.

## Success Criteria

- Remove or rewrite current docs/comments that imply `/tmp/novaic-cortex-sandbox-*` backing paths are stable authority.
- Remove or rewrite current docs/comments that imply in-process locks, process-local state, or file walks are production authority.
- Keep historical docs only if their historical status is explicit from path/title/body.
- Update architecture guard docs with the forbidden-residue patterns.
- Static doc/code comment audit has no unclassified current residue.
