# Business/subscriber code dependency boundary audit ticket

## Problem Definition

Business/subscriber production code must keep explicit dependency boundaries: subscriber aggregation decisions should depend on injected config, and subscriber dispatch should not own wake/session/Cortex scope lifecycle. P717 indicated the obvious aggregation path is likely clean, but this needs a focused code audit and tests/scans.

## Proposed Solution

Scan and inspect active Business/subscriber code for dynamic env reads inside decision logic, direct Cortex/scope/session lifecycle writes, direct Queue/session ownership, or hidden Gateway/device ownership leaks. Patch safe code residue if found. If code is already clean, record exact evidence and run focused guard tests.

## Acceptance Criteria

- Active subscriber aggregation path is proven to use injected config rather than dynamic env reads.
- Active subscriber dispatch path is proven not to mutate Cortex scope input ownership or wake/session lifecycle.
- Business does not proxy Queue task/session ownership in active code.
- Test-only env reads and historical fixtures are classified separately.
- Relevant Business guard tests or focused Python checks pass.

## Verification Plan

Use `rg`/`nl` to inspect Business/subscriber code and tests. Run relevant focused tests such as `novaic-business/tests/test_im_aggregation.py`, `test_pr153_lifecycle_guardrails.py`, and `test_pr117_task_proxy_removed.py` if available. Use compile/import checks if full tests are not practical.

## Risks

- Tests may require dependency setup not present in the current shell; if so, record the blocker and use narrower static/import verification.
- Over-cleaning test helpers could remove useful regression coverage.

## Assumptions

- Production Business/subscriber code lives under `novaic-business/main_business.py`, `main_subscriber.py`, and `novaic-business/business/**`.
- Runtime/Queue ownership should not be implemented in Business/subscriber code except by submitting dispatch requests to Queue.
