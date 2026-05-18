# PR-96 — Make `chat_reply` output standard Markdown

| Field | Value |
| --- | --- |
| **Ticket** | PR-96 |
| **Status** | `[✓]` |
| **Scope** | `novaic-business`, `novaic-cortex`, `novaic-common`, `novaic-agent-runtime` |
| **Depends on** | PR-95 |
| **Invariant** | Chat UI renders standard Markdown. The model must not rely on single-newline pseudo-layout inside `chat_reply.message`. |

## Problem

`chat_reply.message` data preserves literal newlines, and the execution-log monitor displays them with pre-wrap. The Chat message renderer, however, correctly renders message content as standard Markdown, where a single newline inside a paragraph is a soft break and may collapse visually. When the model emits pseudo-layout like `标题\n项目1\n项目2`, Chat appears to lose line breaks even though the stored message is intact.

## Goal

Make the LLM-visible contract explicit:

- `chat_reply.message` is user-visible standard Markdown.
- Multi-item content must use real Markdown lists, tables, or paragraphs.
- Paragraphs must be separated with a blank line.
- The model must not rely on single newlines to create visual layout.

## Non-Goals

- Do not add `remark-breaks` or otherwise change Chat Markdown semantics.
- Do not make Chat render Markdown as pre-wrap plain text.
- Do not mutate or rewrite stored historical messages.
- Do not change execution-log monitor rendering.

## Implementation Checklist

- [x] Add the standard-Markdown reply contract to default behavior prompt text.
- [x] Add the same contract to the canonical Cortex `chat_reply` tool schema.
- [x] Align the common tool definition copy so older schema consumers do not drift.
- [x] Add or update prompt/tool contract tests.
- [x] Confirm runtime prompt assembly preserves the contract when drive defaults are supplied.

## Unit / Contract Tests

- [x] Business prompt contract test asserts standard Markdown reply rules.
- [x] Cortex tool schema test asserts `chat_reply` advertises Markdown layout rules.
- [x] Common tool definition test asserts the aligned `chat_reply` copy.
- [x] Runtime prompt contract test asserts injected behavior guide includes Markdown rules.

## Smoke Test

- [x] Run targeted Business, Cortex, Common, and Runtime tests.
- [x] Inspect deployed prompt/schema files showing the LLM sees the Markdown contract.

## Deployment Checklist

- [x] Deploy affected backend services after tests pass.
- [x] Verify service health/logs after deployment.
- [x] Verify deployed Business and Cortex/Common files contain the Markdown contract.

## GitHub / Commit Checklist

- [x] Commit subrepo changes.
- [x] Push subrepo branch.
- [x] Bump parent repo submodule pointers / docs and commit.

## Rollback

Revert the prompt/schema/test commits. Chat rendering behavior is unchanged by this PR.
