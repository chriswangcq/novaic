# Hidden input remediation tests and guards ticket

## Problem Definition

P469 remediation needs final tests and guards proving the hidden-input cleanup is real across the react saga config work, not merely locally compiled.

## Proposed Solution

Run focused test suites for react finalization/routing and runtime explicit contracts. Re-run guards for direct `ServiceConfig.MAX_*` reads, raw env reads in runtime queue/task code, and old global monkeypatch patterns in focused tests. Save logs under `.complex-problems/L20260516-222011/tmp/p474/`.

## Acceptance Criteria

- Focused pytest suite passes.
- Guard artifacts prove no direct decision-path `ServiceConfig.MAX_*` reads remain.
- Guard artifacts prove no runtime queue/task raw environment reads remain.
- Guard artifacts prove old focused-test monkeypatch patterns are gone.

## Verification Plan

Use pytest plus `rg`/sliced source guards. Record exact artifact paths and outcomes.

## Risks

- A broad `rg` guard may flag the intended `react_config.py` provider boundary; the result must distinguish provider-boundary hits from decision-path hits.

## Assumptions

- Full repo test suite is not required at this child; aggregate parent checks can decide whether to broaden.
