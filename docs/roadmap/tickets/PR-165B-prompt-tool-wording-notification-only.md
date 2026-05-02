# PR-165B — Prompt and Tool Wording Notification-Only Cutover

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-business`, `novaic-common`, docs |
| Depends on | PR-165A |
| Theme | Prompt contract |

## Goal

Make Business prompt text and LLM-visible tool descriptions match the new
subject/environment model. The prompt should say the agent receives
Environment notifications, not already-observed IM bodies.

## Plan

1. Update Business prompt sections that still describe raw IM body injection.
2. Ensure behavior guide tells the model to call `im_read` before answering
   message-triggered wakes.
3. Keep authority prompt direct; only environment events are notification-only.
4. Add prompt snapshot/contract tests that fail on old IM-header-body wording.
5. Smoke a prompt preview/LLM request and confirm wording alignment.
6. Deploy, verify, and commit.

## Required Tests

- Business prompt unit test forbids the old “实际消息内容 already in content”
  contract.
- Business prompt unit test requires notification + `im_read` wording.
- Common tool schema tests continue to pass.

## Done Criteria

- Prompt and tools describe one path: notification -> `im_read` observation.
- No Business prompt text implies unobserved message bodies are already facts.
- Tests, smoke, deploy, and git commit evidence are recorded here.

