# Ticket: make runtime finalizer direct-reply fixtures explicitly legacy-negative

## Problem Definition

`test_pr48_turn_finalizer.py` intentionally uses old direct `im_reply` calls as negative fixtures, but one docstring still describes a shell reply case as `im_reply-only`, and the legacy constants are not centralized.

## Proposed Solution

- Introduce explicit legacy direct reply fixture constants/helpers.
- Keep current success paths on shell `agentctl im reply`.
- Fix comments/docstrings that use `im_reply` when they mean shell reply.

## Acceptance Criteria

- Old direct reply names appear only through explicitly named legacy fixtures.
- Shell reply behavior is described as shell/agentctl behavior.
- Focused finalizer test passes.

## Verification Plan

- `rg` over `test_pr48_turn_finalizer.py`.
- Run focused finalizer test.

## Risk

Do not change the finalizer behavior under test; this is fixture clarity only.
