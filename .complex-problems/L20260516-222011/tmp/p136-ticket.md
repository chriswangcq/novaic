# Audit and harden tool result refs

## Problem Definition

Runtime tool results are projected into Cortex step files, context events, monitor output, and LLM context. The join keys must stay unambiguous: `step_ref` should identify the durable step lookup location, while `payload_ref` should identify the actual payload storage, including externalized blob payloads. Any conflation can make display/blob/tool-output paths appear to work while later context assembly reads the wrong object.

## Proposed Solution

Map runtime tool result creation and Cortex projection code around `step_ref`, `payload_ref`, durable payloads, blob artifact refs, and formatted step reads. Document the intended contract, add or tighten focused tests for externalized payload lookup, and fix any ambiguous key handling if found.

## Acceptance Criteria

- Runtime tool output wrappers, step write paths, Cortex step index/projection paths, and formatted step read paths are mapped.
- Stable `step_ref` versus actual/externalized `payload_ref` contract is explicitly documented in the result.
- Tests prove stable step lookup still works when payload contents are externalized or represented by blob/artifact references.
- Ambiguous duplicate key behavior is either fixed in this problem or split into smaller focused follow-ups.

## Verification Plan

- Search for `step_ref`, `payload_ref`, `durable_payload`, `read_step_formatted`, `write_step`, `artifact`, and `tool-output.v1`.
- Run focused Cortex/runtime tests for step index, tool wrapper, display/image projection, and step formatted reads.
- Add missing tests if a live ambiguity is found.

## Risks

- Some refs may be intentionally duplicated for legacy compatibility; do not leave compatibility branches unclassified.
- The display path is sensitive because it can affect both monitor projection and provider multimodal input.

## Assumptions

- `step_ref` is the stable identity for a tool step.
- `payload_ref` can equal `step_ref` for inline/local payloads but should be allowed to point elsewhere when payload data is externalized.
