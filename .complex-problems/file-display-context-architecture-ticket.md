# Design file/display artifact context architecture

## Problem Definition

The current slow execution symptom exposes a deeper architecture question: large visual and tool artifacts should not behave like ordinary chat text. We need to decide how files, Blob refs, Cortex payloads, `display`, monitor UI, and LLM prompt assembly should fit together so the agent can intentionally inspect resources without accidental prompt bloat.

## Proposed Solution

Perform a focused architecture analysis against the current code and observed backend behavior. Produce a design that separates artifact storage, artifact presentation, LLM context references, and explicit agent inspection tools. Treat this ticket as a design-only ticket: no implementation or deployment in this turn.

## Acceptance Criteria

- Explain the ideal dataflow for large artifacts from tool output to Cortex persistence to LLM context to explicit `display` inspection.
- Explain what should be stored inline, what should be stored by reference, and what should be display-expanded.
- Explain how this relates to agent autonomy and the environment/tool boundary without relying on subjective LLM behavior claims.
- Identify invariants that would prevent base64/history bloat.
- List concrete migration phases and tests.

## Verification Plan

- Inspect current Runtime/Cortex code paths around `display_files`, `payload_ref`, `format_for_llm`, and `expand_messages_for_llm`.
- Compare the proposed model against the observed backend slow-path evidence.
- Record a result and success check in the ledger.

## Risks

- The design may overcorrect by hiding too much visual context from the model.
- The design may conflate user-visible monitor display with model-visible LLM context.
- Existing Blob/Cortex abstractions may need compatibility bridges during migration.

## Assumptions

- This turn is for architecture thinking and recommendation, not code implementation.
- Large visual artifacts should remain accessible to the agent, but access should be explicit and bounded.
