# PR-173 — Environment IM History Observation Tools

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-common`, `novaic-business`, `novaic-agent-runtime`, docs |
| Depends on | PR-167, PR-168 |
| Theme | Explicit Environment observation |

## Goal

Add explicit LLM tools for Agent-controlled IM history observation without reviving the retired `chat_history` path.

## Current-State Analysis

`im_read` covers current wake notifications. The Agent cannot yet intentionally browse prior Environment IM context. The architecture document records the desired tools as `im_history`, `im_search`, and `im_context`.

## Implementation

- Add canonical schemas in `novaic-common/common/tools/environment.py`.
- Expose the schemas through the built-in LLM tool list.
- Add Business internal Environment endpoints:
  - `/internal/environment/{agent_id}/im/history`
  - `/internal/environment/{agent_id}/im/search`
  - `/internal/environment/{agent_id}/im/context`
- Add repository/service methods over `environment-im-messages`.
- Add Runtime executors that call the Business endpoints.
- Keep results bounded and percept-like; do not auto-inject history into prompt.

## Tests / Smoke

- Common schema/executor alignment.
- Business repository/service tests for history/search/context ordering and bounds.
- Runtime executor tests for endpoint shape and validation.
- Retired `chat_history` guard must stay passing.

## Closure

- `im_history`, `im_search`, and `im_context` are now in Common LLM schemas, Business Environment internal APIs, Runtime executors, and product-semantics guards.
- Tests passed:
  - `novaic-common`: `PYTHONPATH=.:../novaic-agent-runtime pytest -q`
  - `novaic-business`: `PYTHONPATH=. pytest -q`
  - `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q`

## Deploy / GitHub

- Deploy services after tests pass.
- Commit and push touched repos plus parent submodule pointers.
