# PR-171C — Remove Retired Tool-name Aliases

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Parent | [PR-171](PR-171-final-old-path-physical-deletion.md) |
| Repos | novaic-cortex, novaic-app, docs |
| Theme | Old tool alias deletion |

## Current-State Analysis

The active LLM communication tools are `im_reply` / `im_send` plus `subagent_spawn`. Cortex trace projection still recognized the retired `chat_reply` name as a reply alias, which keeps an old tool identity alive even after schema/executor deletion.

## Plan

- Remove `chat_reply` from Cortex trace projection reply aliasing.
- Add a regression test proving retired names project as generic unknown tool actions rather than active product semantics.
- Update current architecture docs to use `im_reply` and Activity Timeline wording.

## Verification Required

- [x] Cortex trace projection tests.
- [x] Cortex full test suite.
- [x] Current docs residue scan.
- [x] Services deployment.
- [x] GitHub commit for `novaic-cortex` and parent docs/submodule pointer.

## Closure Evidence

- Cortex trace projection no longer treats retired `chat_reply` as a first-class reply action; `im_reply` is the only reply semantic.
- Current architecture docs now describe `im_reply`, Environment notifications, Cortex Activity Timeline, and Common canonical tool schemas.
- `cd novaic-cortex && PYTHONPATH=.:../novaic-common pytest -q tests/test_trace_projection.py tests/test_tool_schemas_limits.py tests/test_payload_inspection_api.py` → 23 passed.
- `cd novaic-cortex && PYTHONPATH=.:../novaic-common pytest -q` → 401 passed, 16 skipped.
