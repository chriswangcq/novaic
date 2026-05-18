# Map and verify explicit Cortex payload inspection APIs

## Problem Definition

Cortex payload inspection APIs should require explicit payload references and bounded operation inputs. They must not be mistaken for default context assembly.

## Proposed Solution

Locate payload read/search/summarize/qa implementations and tests. Verify API inputs and bounds, and classify summarize/qa as explicit interpretation actions.

## Acceptance Criteria

- Payload API functions/routes are mapped.
- Bounded read/search behavior is verified.
- Summarize/qa APIs are explicit payload actions.
- Tests cover bounded behavior.

## Verification Plan

Use targeted `rg` over Cortex payload API code/tests, inspect line-numbered ranges, and run payload inspection tests.

## Risks

- APIs may use wrappers/generic handlers; follow call sites carefully enough to avoid false confidence.

## Assumptions

- Explicit summarize/qa over payload is allowed because it is user/tool-triggered, not automatic history assembly.
