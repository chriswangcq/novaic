# PR-60 — User IM content must render as clean user text, not a Python dict string

| Field | Value |
|---|---|
| **Ticket** | PR-60 |
| **Status** | `[✓]` 2026-04-25 — implemented, tested, deployed |
| **Opened** | 2026-04-25 |
| **Owner** | __ |
| **Severity** | P1 user-message fidelity — the model receives transport-shaped text instead of the user's actual utterance. |
| **Blocks** | High-quality chat behavior, attachment semantics, and reliable IM aggregation. |
| **Blocked by** | PR-38 provides IM header baseline; this ticket covers body fidelity on top. |
| **Invariant** | The LLM-visible body after the IM header should be the user's message text, with attachments represented intentionally rather than as raw object repr. |

## Bug

The latest user message is rendered to the model as:

```text
{'text': '你会干啥', 'attachments': []}
```

The user-facing utterance is just:

```text
你会干啥
```

The current body looks like a Python `dict` repr and leaks transport structure into the prompt.

## Evidence

Source: user-provided LLM request snapshot on 2026-04-25 15:37 Asia/Shanghai:

```text
[msg_id=195c7b2105d8 from=user:155cc065-d462-413d-a60c-406b64a8bc84 at=2026-04-25T07:37:42.602Z]
{'text': '你会干啥', 'attachments': []}
```

## Impact

- The model must infer which part is real user text and which part is transport metadata.
- Empty attachments add noise to every user message.
- Non-empty attachments may become ambiguous or be rendered inconsistently.

## Acceptance Criteria

- Plain text user messages render as plain body text after the IM header.
- Empty attachment arrays are omitted from the LLM-visible body.
- Non-empty attachments have an explicit, stable, LLM-readable representation.
- Snapshot coverage includes Chinese text, empty attachments, and at least one attachment case.

## Out of Scope

This ticket intentionally does not specify a repair method.
