# PR-163A — Environment Tool Schema Candidates

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-163 |
| Repos | `novaic-common`, docs |
| Depends on | PR-162 |

## Goal

Create a shared schema source for future Environment tools without exposing them to LLM calls yet.

Candidate tools:

- `im_read`: observe pending/current Environment IM notifications.
- `im_reply`: send a user-visible reply through Environment.
- `im_send`: send an IM to another agent/subagent through Environment.

## Implementation Plan

1. Add a dedicated Common schema source for Environment tools.
2. Add tests proving schema shape and product language.
3. Add a guard that candidate tools are not active LLM tools until PR-163B/PR-163C finish executor and product-surface work.

## Tests

- Unit: `PYTHONPATH=. pytest tests/test_environment_tool_schemas.py tests/test_tool_definitions_contract.py tests/test_tool_product_semantics_contract.py` — 13 passed.
- Full common smoke: `PYTHONPATH=.:../novaic-agent-runtime pytest` — 112 passed.

## Deploy / Git

- Deploy: `./deploy services` — all backend services restarted successfully.
- Production smoke: Environment candidate tool names were readable and did not intersect active LLM tool names.
- Git: `novaic-common` commit `ef35576 feat(common): add environment tool schema candidates`.

## Done Criteria

- [x] Candidate schemas exist and are tested.
- [x] Active LLM tool list is unchanged.
- [x] No Runtime executor or prompt behavior changes in this ticket.

## Evidence

- Files added:
  - `common/tools/environment.py`
  - `tests/test_environment_tool_schemas.py`
- `common/tools/__init__.py` exports candidate schema helpers.
