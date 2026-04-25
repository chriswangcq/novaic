# LLM Call Contract Feature Backlog

| Field | Value |
|---|---|
| **Status** | Draft |
| **Created** | 2026-04-25 |
| **Owner** | __ |
| **Scope** | Improvements that are not immediate bugs, but would make Cortex/runtime LLM calls easier to reason about, test, and evolve. |

## Background

After the Recall cleanup and direct `shell` exposure, the latest LLM call is much cleaner than the old recovered-memory payload. The remaining improvement area is not one single fix; it is the contract around "what the model is told", "what tools it can actually call", and "how prior scope state is rendered".

This document intentionally groups feature ideas into one place so they can be discussed later without turning each idea into an urgent bug ticket.

## Candidate Features

### 1. Prompt/tool contract linter

Build a preflight check that compares LLM-visible prompt text against the actual `tools[]` names for the same request. It should catch phantom tool names, stale quick-reference snippets, and role-inappropriate tools before they reach the model.

Desired outcome: a generated LLM call cannot silently contain tool names that the model cannot call.

### 2. Dynamic tool quick reference

Generate the "工具速查" section from the same registry that builds `tools[]`, rather than maintaining a hand-written prompt list.

Desired outcome: adding/removing/renaming a tool updates the prompt reference automatically.

### 3. Role-aware tool bundles

Split tool exposure by agent role and wake type:

- main user-facing agent
- child subagent
- system wake
- simple chat turn
- implementation/debug turn

Desired outcome: the model sees only the tools that make sense for its current role and task.

### 4. Context block budget policy

Define a budget and priority order for `<PREV_SCOPE_HISTORY>`, `<PREV_SCOPE_TAIL>`, current IM messages, active skill stack, and system instructions.

Desired outcome: context growth is predictable, and short prior turns do not get duplicated across blocks.

### 5. Root-scope continuity finalizer

Create a product-level decision for how root turns should produce high-quality future-self summaries even when the model only sends `chat_reply`.

Desired outcome: `<PREV_SCOPE_HISTORY>` is useful by default, not dependent on perfect model discipline.

### 6. Clean IM body and attachment rendering

Standardize how `content.text`, empty attachments, non-empty attachments, and future rich-message fields render after the IM header.

Desired outcome: the model reads the user's actual utterance first, with attachment data represented intentionally.

### 7. Shell policy tiers

Give `shell` a small, explicit policy model:

- read-only inspection
- local edits/tests
- server mutation
- destructive data operation
- external/network side effect

Desired outcome: the model can reason about command risk without needing a giant procedural rulebook.

### 8. Request parameter normalizer

Normalize provider payloads before dispatch so unset optional fields are omitted and provider-specific defaults remain centralized.

Desired outcome: cleaner snapshots and fewer provider compatibility surprises.

### 9. LLM call snapshot tests

Add golden snapshots for representative turns:

- first greeting
- "what can you do?"
- shell-enabled debugging turn
- child subagent report
- system wake with prior scope history

Desired outcome: prompt drift becomes visible in review.

### 10. LLM-call observability

Log compact metadata for every LLM request:

- tool names
- context block names and token estimates
- model id
- provider
- optional parameter keys actually sent
- whether previous scope history/tail were present

Desired outcome: production debugging can answer "what did the model actually see?" without dumping full prompt content into logs.

## Discussion Notes

- The highest leverage features are likely the prompt/tool linter, dynamic quick reference, and snapshot tests. They prevent future regressions instead of only cleaning one prompt.
- Role-aware tools become more important now that `shell` is exposed directly.
- Root-scope summary quality is the main open design question for R9 continuity after removing old Recall-style injection.

## Non-Goals

- This document is not a repair ticket.
- It does not prescribe implementation order.
- It does not replace the individual bug tickets PR-56 through PR-63.
