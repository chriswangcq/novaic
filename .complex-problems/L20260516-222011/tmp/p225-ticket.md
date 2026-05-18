# Map runtime LLM step-ref expansion flow

## Problem Definition

The runtime must resolve tool `step_ref` values through the Cortex formatted projection API rather than inserting raw durable payloads into LLM messages.

## Proposed Solution

Inspect the runtime LLM preparation and step result client code paths. Record the function chain, projection decision inputs, and evidence that raw durable payloads stay behind Cortex step/payload APIs.

## Acceptance Criteria

- Function/file chain from LLM preparation to Cortex formatted step read is documented.
- Projection decision inputs are documented.
- Raw durable payload is not directly inserted by this path.

## Verification Plan

Read line-numbered source slices from runtime context preparation and step result client, plus tests that exercise expansion.

## Risks

- Similar helper names can make it easy to confuse preview/summary expansion with LLM expansion.

## Assumptions

- This is an audit-only ticket unless the path inspection reveals a direct raw-payload insertion bug.
