# PR-156B — Remove Wake Finalizer Env Branch Switches

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Parent | [PR-156](PR-156-deploy-config-overlay-residue-review.md) |
| Repos | novaic-agent-runtime |

## Goal

Remove env-driven alternate branches from wake finalization. The active behavior
should be a code-level invariant: `chat_reply` is the turn closer and the LLM
closes the current wake scope with `skill_end(report=...)`.

## Scope

- Remove `WAKE_TURN_FINALIZER_ENABLED`.
- Remove `WAKE_TURN_CLOSER_TOOLS`.
- Update unit tests to assert fixed behavior instead of testing fallback knobs.
- Remove comments/docs that describe the retired rollback lever as active.

## Tests / Guardrails

- Run `novaic-agent-runtime` turn-finalizer tests.
- Add/extend lint to fail if retired wake finalizer env names return.

## Smoke / Deploy

- Deploy runtime after tests.
- Verify `./deploy status`.

## Git

- Commit independently if tests and deploy pass.
