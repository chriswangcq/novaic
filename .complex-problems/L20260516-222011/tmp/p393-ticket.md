# Normalize round and stack-depth defaults

## Problem Definition

Wake finalize and recovery paths still default stack-depth and round-number metadata with raw `int(... or 0)`. These are not session generation, but they are control-plane diagnostics and should not silently accept bool/malformed values.

## Proposed Solution

Patch wake finalize and recovery metadata parsing to use explicit non-negative integer helpers for `stack_depth_at_finalize` and `round_num`, preserving missing-value defaults while rejecting bool/malformed values. Add focused tests if existing coverage can exercise the helpers directly.

## Acceptance Criteria

- `wake_finalize.py` no longer uses raw `int(ctx.get("stack_depth_at_finalize") or 0)`.
- `session_recovery.py` no longer uses raw `int(recovery_metadata.get("stack_depth_at_finalize") or 0)` or raw `round_num` parsing.
- Focused wake finalize/recovery tests pass.
- Final classification distinguishes these defaults from session generation authority.

## Verification Plan

Run compile checks, focused wake finalize/recovery tests, and targeted source guards for stack-depth/round defaults.

## Risks

- Missing values should still default to `0`; only malformed explicit values should fail.

## Assumptions

- Bool values for stack depth or round number are malformed and should not be accepted as `0` or `1`.
