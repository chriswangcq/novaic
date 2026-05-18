# Map final active stack message injection ordering

## Problem Definition

The active stack projection becomes a final `[Active skill stack ...]` system message. P181 must map the exact injection code and ordering relative to prepared messages, tool result expansion, display projection, and provider message formatting.

## Proposed Solution

Search and inspect runtime context preparation and provider request assembly code for active stack message injection. Trace whether the system message is appended before or after tool-result expansion, and whether current-round display detection relies on position or explicit round/tool-call metadata. Run focused tests around context preparation and stack injection.

## Acceptance Criteria

- Active stack injection source in final LLM messages is identified.
- Ordering relative to assistant tool calls, tool results, step-ref expansion, and provider formatting is documented.
- Tests prove the ordering does not by itself convert current tool output to historical output.
- Any duplicate or stale final-injection path is removed or split.

## Verification Plan

Use `rg` and source reads for the active stack literal and message assembly. Run focused runtime tests around context preparation, no-tool warning/stack messages, provider LLM request smoke guardrails, and display projection if relevant.

## Risks

- The injection path may be split between runtime and LLM factory request logging, so source mapping must distinguish durable context from provider-request formatting.

## Assumptions

- P180 already proved the stack state source of truth; P181 focuses only on final message injection and ordering.
