# Rewrite Cortex Root RW Scratch Fixtures

## Problem Definition

P635 identified multiple Cortex tests that use `/rw/scratch` as a convenient generic writable fixture path. After P638 removed root scratch from the default layout, these tests should stop making global `/rw/scratch` look canonical. Tests that need true scratch semantics should use `/rw/subagents/main/scratch`; tests that only need arbitrary writable files should use neutral `/rw/tmp` or `/rw/public` depending shell visibility needs.

## Proposed Solution

Rewrite Cortex test fixture paths in batches: workspace/path-authority tests, runtime/path-abuse tests, and metrics/chaos/tool tests. Preserve each test's original invariant and keep `test_sandboxd_wiring.py` subagent scratch tests intact.

## Acceptance Criteria

- Cortex tests no longer use root `/rw/scratch` as a generic fixture path.
- Path normalization and abuse tests still check the same security/normalization behavior using updated paths.
- Runtime tests that need shell-visible files use a path mounted by the current RW working-set policy.
- Focused tests for all touched files pass.

## Verification Plan

Run post-change `rg -n "/rw/scratch" novaic-cortex/tests novaic-cortex/novaic_cortex`, then run focused tests for touched files.

## Risks

- Some tests depend on `.keep` or tree listing behavior; replacing `/rw/scratch` with `/rw/tmp` changes initialized directory assumptions.
- Runtime shell-visible fixtures should not use `/rw/tmp` if the shell working set excludes historical `/rw/tmp`.

## Assumptions

- Root `/rw/scratch` should disappear from Cortex tests except possibly adversarial strings if explicitly justified.
