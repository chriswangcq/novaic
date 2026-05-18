# P032 Check

## Judgment

Success.

## Evidence Reviewed

- `novaic-common/common/config.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/scripts/check_cortex_boundary.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`

## Stress Check

I looked for the original failure mode: internal comments, config descriptions, or guard labels still naming `im_reply` as the active user-visible reply path. The edited files now describe the concept as a user-visible reply action instead of naming the direct legacy tool.

The boundary guard still detects the legacy token without exposing it as ordinary architecture vocabulary, by constructing the legacy token in code for detection rather than documenting it as the expected path.

## Residual Risk

This ticket only covers the targeted internal reply-cap wording. Broader direct-tool residue is still tracked by parent problem `P015` and should be checked separately.
