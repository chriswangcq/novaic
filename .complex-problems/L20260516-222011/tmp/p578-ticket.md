# Classify Runtime Message Assembly And Active Stack Ordering

## Problem Definition

P578 must audit runtime message assembly before provider serialization, including context preparation, assistant/tool messages, active skill stack/system injection, and history ordering, to determine whether any path can place raw media/base64 or harmful ordering into the LLM request.

## Proposed Solution

Run targeted scans for message assembly, context preparation, request message lists, tool-result message content, active stack injection, and ordering logic. Capture outputs, focused slices, and classify findings as intended, risky, removable, or follow-up.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Relevant code/test slices have line references.
- Tool-result, assistant, system/active-stack, and history-ordering projections are classified.
- Any active-stack ordering risk to current-turn image/display delivery is explicitly judged.
- Any high-confidence risky residue is forwarded to P554 remediation.

## Verification Plan

Search `novaic-agent-runtime` for context preparation, message list construction, active skill stack prompts, `tool_call_id`, `role: tool`, `_mcp_content`, and request body assembly. Inspect focused slices and compare against recent request-body symptoms.

## Risks

- Search terms may hit logs/tests rather than active request assembly.
- The active stack may be visually suspicious but harmless if provider adapters handle images correctly.

## Assumptions

- Provider serialization is handled separately by P579.
- Display tool implementation is handled separately by P575.

