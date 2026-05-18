# Ticket: clean runtime activity projection fixtures

## Problem Definition

`test_pr193_activity_projection.py` uses direct `im_read` tool calls as normal assistant action fixtures. Current runtime activity should model shell-first `agentctl im read` calls.

## Proposed Solution

- Replace current-path activity projection fixtures with `shell` calls that include an Agent Monitor `desc`.
- Preserve deterministic ordering checks.
- Leave historical direct-tool monitor behavior to `P036`.

## Acceptance Criteria

- `test_pr193_activity_projection.py` no longer uses direct `im_read` as a normal current-path fixture.
- Current-path assertions expect `tool == "shell"` and monitor text from `desc`.
- Focused activity projection test passes.

## Verification Plan

- Focused `rg` over the test file.
- Run `test_pr193_activity_projection.py`.

## Risk

Do not change production activity projection behavior in this ticket; this is test fixture modernization only.
