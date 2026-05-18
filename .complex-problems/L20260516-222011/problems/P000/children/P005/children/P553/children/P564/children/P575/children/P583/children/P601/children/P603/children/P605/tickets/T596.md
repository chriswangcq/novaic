# Ticket: Collect Exact Backend Preview Evidence

## Problem Definition

P603 needs exact evidence, not just broad inventory, that backend Agent Monitor/progress preview paths use bounded text and references instead of raw image/base64 payloads, and that this monitor surface is separate from the LLM display-perception request path.

## Proposed Solution

Append line-numbered code slices for Cortex step preview APIs, payload inspection APIs, payload externalization/indexing, and Business Agent Monitor/progress schemas or event boundaries. Then run focused tests that cover payload externalization, bounded payload preview/read behavior, and Agent Monitor timeline/action separation. Record whether any located monitor/progress path can carry raw image bytes.

## Acceptance Criteria

- Exact `nl -ba` slices are captured for each required backend surface.
- Focused pytest output is captured for the directly relevant boundary tests.
- The result explicitly states whether backend monitor/progress events can carry raw image bytes or base64.
- The result maps evidence to the original P603 criteria and states residual risk.

## Verification Plan

Use read-only source inspection plus focused pytest runs. Treat missing tests, failing tests, or any raw image/base64 monitor path as evidence requiring another follow-up rather than passing the check.

## Risks

- Test names may differ from the initially guessed names; discover exact tests with `rg` if needed.
- Some monitor surfaces may be schema-only, so the evidence must distinguish product/UI projection from LLM request construction.

## Assumptions

- This ticket is evidence-gathering only and should not change production code unless the inspection finds a clear bug that must be spawned as a separate runtime child problem.
