# Check: P463 side-effect bypass final guard

## Result IDs

- R451

## Status

success

## Evidence

- R451 saves final guard and focused test artifacts.
- Focused tests passed: `33 passed`, exit `0`.
- Observed-wake obsolete production guard section is empty.
- Retained direct calls are classified as generic APIs, dispatcher internals below durable rows, saga-outbox internals, saga definitions, or assembly code.

## Criteria Map

- Save guard artifacts: satisfied.
- Confirm no dangerous live bypass remains: satisfied by R451 classification.
- Route unclassified hit into follow-up: not needed; no unclassified hit remains.
- Focused tests pass: satisfied.

## Execution Map

- Reviewed R451 guard classifications and test evidence.
- Checked the result does not hide route-level generic APIs as session side-effect ownership.
- Performed no source changes during this check.

## Stress Test

The guard intentionally catches broad direct publish/create calls. I checked that each retained hit is either outside session-specific ownership or below an outbox-owned dispatcher/saga-outbox owner. This is stricter than just checking test pass.

## Residual Risk

No P463 bypass gap remains.
