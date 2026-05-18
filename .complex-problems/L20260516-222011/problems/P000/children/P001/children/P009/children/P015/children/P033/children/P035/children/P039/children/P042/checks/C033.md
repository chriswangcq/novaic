# P042 Check

## Judgment

Success.

## Evidence Reviewed

- Result `R024`.
- Focused finalizer test run.
- Focused grep for `im_reply` in `test_pr48_turn_finalizer.py`.

## Stress Check

The remaining direct reply token is centralized as a `LEGACY_DIRECT_REPLY_TOOL` fixture and appears in legacy-negative test names. Current success-path tests use shell `agentctl im reply` commands and no longer describe that path as `im_reply-only`.

## Residual Risk

Runtime activity projection tests and guard assertions are intentionally left to sibling problems.
