# Ticket: classify Cortex test direct-tool vocabulary

## Problem Definition

Cortex tests still contain direct-tool names, mainly in schema denylist tests. After earlier endpoint/counter cleanup, confirm whether any generic fixture remains.

## Proposed Solution

- Scan Cortex tests.
- If remaining hits are negative shell-capability/schema-denylist assertions, keep them and record the classification.
- If any generic fixture remains, replace it with shell/API vocabulary.

## Acceptance Criteria

- Cortex tests do not use old direct tools as current happy-path fixtures.
- Remaining old names are explicit negative schema checks.
- Focused Cortex tests pass.

## Verification Plan

- Focused `rg` over `novaic-cortex/tests`.
- Run schema/payload/wake focused tests.

## Risk

Do not remove guard assertions that prove migrated tools are not LLM schemas.
