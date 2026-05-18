# Ticket: Audit Display History and Perception Regression Tests

## Problem Definition

Display media handling now depends on several contracts: current-turn `display` can become real image content for the LLM, history replay must stay text/reference-only, durable tool text must not persist raw base64, and active-stack/system messages must not accidentally block current display perception. We need an explicit test inventory that proves these contracts are covered or names the gaps.

## Proposed Solution

Scan display-related runtime and Cortex tests, then map each invariant to concrete test names and focused test commands. If a contract has no direct test, record a precise follow-up instead of assuming coverage.

## Acceptance Criteria

- Exact scan commands and test commands are recorded.
- Current-turn display image injection has direct test coverage or a follow-up.
- Historical display replay staying text/reference-only has direct test coverage or a follow-up.
- Durable shell/display output avoiding raw base64 has direct test coverage or a follow-up.
- Active-stack/system-message ordering around display perception has direct test coverage or a follow-up.
- Missing or weak coverage is forwarded to the aggregate verification path instead of being hidden in prose.

## Verification Plan

Run read-only test inventory scans with `rg`, inspect relevant test slices with `nl -ba`, and run the smallest focused test subset that exercises the mapped contracts.

## Risks

- Some coverage may be split across runtime and Cortex tests; the inventory must cite both sides rather than over-crediting one test.
- Full test suites may contain unrelated failures; focused command results should distinguish contract failures from known unrelated failures.

## Assumptions

- The current display behavior from P584/P586 is the target behavior to protect.
- This ticket is an audit/test-inventory task first; implementation follow-ups should be created only for concrete missing coverage.
