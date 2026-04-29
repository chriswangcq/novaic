# PR-99 — Prompt contract fragments SSOT

| Field | Value |
| --- | --- |
| **Ticket** | PR-99 |
| **Status** | `[ ]` |
| **Scope** | `novaic-business`, `novaic-agent-runtime` |
| **Depends on** | PR-98 |
| **Invariant** | LLM-visible core contract text must not drift between Business defaults and Runtime prompt assembly. |

## Problem

Business owns default prompt sections, while Runtime owns prompt shell, IM semantics, and `NO_TOOL_WARNING`. These are all LLM-visible contract text but currently live in separate places.

## Goal

- Identify core prompt contract fragments.
- Add cross-module guardrails for wake scope, `skill_end(report=...)`, tool truthfulness, Markdown reply rules, and no legacy summary paths.
- Reduce duplicated wording where practical without making the prompt system rigid.

## Non-Goals

- Do not move all prompt prose into a database migration.
- Do not remove agent-customizable prompt fields.
- Do not reintroduce memory/task/autonomy templates.

## Checklist

- [ ] Add prompt contract fragments or a shared contract test fixture.
- [ ] Add Business and Runtime tests that assert the same invariants.
- [ ] Run targeted prompt tests.
- [ ] Deploy affected backend service if default prompt changes.
- [ ] Commit, push, and bump parent repo.

