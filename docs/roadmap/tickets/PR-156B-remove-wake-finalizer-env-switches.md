# PR-156B — Remove Wake Finalizer Env Branch Switches

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Parent | [PR-156](PR-156-deploy-config-overlay-residue-review.md) |
| Repos | novaic-agent-runtime |

## Goal

Remove env-driven alternate branches from wake finalization. The active behavior
should be a code-level invariant: `chat_reply` is the turn closer and the LLM
closes the current wake scope with `skill_end(report=...)`.

## Scope

- [x] Remove `WAKE_TURN_FINALIZER_ENABLED`.
- [x] Remove `WAKE_TURN_CLOSER_TOOLS`.
- [x] Update unit tests to assert fixed behavior instead of testing fallback knobs.
- [x] Remove comments/docs that describe the retired rollback lever as active.

## Tests / Guardrails

- [x] `python3 -m pytest tests/test_pr48_turn_finalizer.py tests/test_runtime_tool_path_contract.py -q`
- [ ] Add/extend lint to fail if retired wake finalizer env names return. Covered in PR-156C.

## Smoke / Deploy

- [x] Deploy runtime after tests.
- [ ] Verify `./deploy status` after the PR-156 batch.

## Git

- Commit independently if tests and deploy pass.
