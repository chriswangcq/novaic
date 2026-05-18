# Audit runtime LLM prepare caller authority

## Problem Definition

Runtime LLM message assembly must be proven to use the Cortex prepare/read-model contract rather than legacy `context/read` or raw `context.jsonl` projection files as authority. The immediate risk is a split-brain context path: Cortex could correctly externalize or normalize context, while the runtime still assembles provider messages from an older projection path.

## Proposed Solution

Map the runtime caller chain from LLM task handling to Cortex context preparation, then inspect the bridge and tests that enforce that chain. Verify whether runtime uses `/v1/context/prepare_for_llm` or an explicit equivalent bridge call, and whether any `read_context`/`context/read` usage can still feed provider messages. If a gap is found, fix the caller path or split the discovered gap into a narrower follow-up problem before recording success.

## Acceptance Criteria

- Runtime LLM prepare-context caller path is identified with concrete file/function pointers.
- Provider-message assembly is proven to use the explicit Cortex prepare contract.
- Any `read_context` usage in runtime is classified as non-authoritative for LLM provider message assembly, or fixed/split if it is authoritative.
- Verification includes targeted tests or residue guards that fail if runtime LLM assembly regresses to `read_context` as authority.

## Verification Plan

- Search runtime sources for `prepare_for_llm`, `prepare_context`, `read_context`, `context/read`, and LLM assembly entry points.
- Inspect the concrete caller chain in runtime code, not just docs.
- Run the narrow runtime tests covering context preparation, explicit contracts, and LLM prompt/prepare guardrails.
- Record source pointers, test commands, and residual risk in the ticket result.

## Risks

- A helper named `read_context` may be used for non-LLM bookkeeping; do not over-delete without classifying the caller.
- Runtime tests may not cover the exact provider-message assembly edge, requiring a focused guardrail test.
- Mixed-package pytest discovery can fail due local `tests` package names; verify per package if necessary.

## Assumptions

- `P156` already established Cortex endpoint/read-model authority; this ticket only covers runtime caller usage.
- If runtime already uses the correct prepare bridge, the implementation work is limited to evidence and guardrails.
- Any legacy path found in active LLM assembly should be treated as a real gap, not a compatibility branch to keep.
