# PR-290C — Session Generation Fallback Hardening

Status: Closed

## Goal

Remove silent generation fallback to `1` where it can break generation checks.

## Closure Notes

- Removed fallback-to-1 behavior from next-generation reads.
- Removed fallback-to-1 behavior from active-generation reads used by attach
  publication.
- Generation read failures now propagate instead of silently weakening
  generation checks.
- Verified with targeted attach/wake/state/generation tests: 14 passed.
