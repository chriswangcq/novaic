# P043 Result

## What Changed

- Replaced current-path direct `im_read` activity projection fixtures in `novaic-agent-runtime/tests/test_pr193_activity_projection.py` with shell `agentctl im read` calls.
- Added a shared `SHELL_READ_MESSAGE_ARGS` fixture with an Agent Monitor `desc`.
- Updated assertions to expect `tool == "shell"` while preserving monitor text `读取消息`.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr193_activity_projection.py`
  - 8 passed
- `rg -n "\\bim_read\\b|\\bim_reply\\b" novaic-agent-runtime/tests/test_pr193_activity_projection.py`
  - no matches

## Remaining Gap

Production activity projection legacy handling remains open in `P036`.
