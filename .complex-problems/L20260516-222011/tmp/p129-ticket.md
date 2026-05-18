# Audit payload API and pointer retrieval boundaries

## Problem Definition

Large tool outputs should be inspected explicitly through payload APIs and pointers, not silently loaded into ordinary LLM context. We need to verify Cortex payload APIs, write paths, normal context assembly, and agent-facing guidance enforce that boundary.

## Proposed Solution

Split the audit into payload API behavior, write/reference path behavior, and agent-facing schema/guidance. Map code and tests, add or tighten tests if gaps are found.

## Acceptance Criteria

- Payload read/search/summarize/qa APIs are mapped and shown to be explicit/bounded/pointer-addressed.
- Tool/step writes preserve payload references and do not inline large outputs into normal context entries.
- Normal LLM context paths do not perform full payload reads by default.
- Tool schema/guidance tells agents to use explicit payload inspection for large outputs.
- Tests cover payload references and bounded retrieval behavior.

## Verification Plan

Inspect Cortex payload APIs/tests, runtime tool step write paths, context expansion, and tool schemas. Run targeted tests for payload inspection and step/payload projection if available.

## Risks

- Summary/QA APIs may intentionally call a model over payload content; classify them as explicit user/tool action, not default context assembly.
- Some older tests may use inline payload text fixtures; distinguish tests from runtime paths.

## Assumptions

- This problem focuses on backend payload/pointer boundaries, not frontend rendering of payload controls.
