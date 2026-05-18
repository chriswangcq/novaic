# Recovery compensation finalize source map

## Problem

Before changing recovery behavior, identify every recovery or compensation path that can synthesize `wake_finalize` or equivalent finalize mutation work. This belongs under P351 because identity hardening cannot be complete if a hidden source path still creates ambiguous finalize tasks.

## Success Criteria

- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, saga compensation code, and related tests.
- Produce a concise source map of every path that creates or replays `wake_finalize` after failure/recovery.
- Identify the source of `scope_id`, wake/root scope path, subagent id, and session generation for each path.
- Mark any ambiguous path as requiring a downstream child fix rather than treating it as safe.
