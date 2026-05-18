# Classify cutover and guardrail test hits

## Problem Definition

P542 owns high-density residue hits in cutover, guardrail, SSOT, and cleanup tests. These tests often intentionally mention retired names to prevent regressions, but stale tests can also preserve misleading expectations.

## Proposed Solution

Filter P531 test hits to the P542 file list, count hits by file, inspect hit contexts, and classify each file by guardrail purpose and stale-residue risk.

## Acceptance Criteria

- All P542-owned files are filtered and counted.
- Each file has a purpose/category rationale.
- Guardrail tests that intentionally mention retired vocabulary are distinguished from tests that preserve stale behavior.
- Any stale or misleading guardrail/cutover test becomes follow-up-worthy.

## Verification Plan

Use P531 test scan lines as the source of truth, produce filtered hit/count/context artifacts, and classify every owned file once. Stress-check for tests that assert the presence of old code instead of asserting its absence.

## Risks

- Guardrail tests deliberately include words like `legacy`, `active_sessions`, and `fallback`, so keyword presence alone is not enough.
- A stale guardrail can create false confidence if it only checks source text rather than behavior.

## Assumptions

- P542 owns the eleven high-density files listed in its split child problem.
