# Attach generation compatibility cleanup ticket

## Problem Definition

P490 must verify and clean active-input attach generation compatibility residue. Attach handling should require expected wake scope and expected session generation; stale or missing generation paths must reject/buffer explicitly instead of silently delivering to the wrong wake.

## Proposed Solution

Audit runtime attach handler, session outbox attach effect builder/publisher, session repository attach-race handling, and tests. Remove or tighten any no-generation compatibility path. Add guard coverage if an important boundary is not already protected.

## Acceptance Criteria

- Attach production paths require expected wake scope and expected session generation.
- Missing/stale generation behavior is explicit and deterministic.
- Any remaining compatibility-looking attach branch is classified or guarded.
- Focused attach/session tests pass.

## Verification Plan

Use `rg` and file inspection over `runtime_handlers.py`, `session_outbox.py`, `session_repo.py`, attach-related tests, and generation contract helpers. Run focused attach/generation tests and save artifacts.

## Risks

- Attach-race buffering is expected behavior and should not be deleted as compatibility residue.

## Assumptions

- No backward-compatible no-generation attach path is needed.
