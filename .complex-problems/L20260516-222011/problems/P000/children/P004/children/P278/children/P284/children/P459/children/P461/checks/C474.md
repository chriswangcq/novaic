# Check: P461 dispatcher direct call classification

## Result IDs

- R448

## Status

success

## Evidence

- R448 classifies all three dispatcher external calls.
- Each classification is tied to durable row fetch/list and ack/fail paths.
- Guard artifact is saved at `.complex-problems/L20260516-222011/tmp/p461/dispatcher-direct-call-guard.txt`.

## Criteria Map

- Save source guard output: satisfied.
- Classify each direct call: satisfied for saga creation, recovery archive publish, and attach input publish.
- Create/fix follow-up if any direct call bypasses durable outbox: not needed; no bypass found inside dispatcher.

## Execution Map

- Reviewed R448 against the P461 problem statement.
- Checked that it does not overclaim P462/P463 scope.
- Performed no implementation during this check.

## Stress Test

The risky interpretation would be “any direct `queue.publish` is bad.” R448 instead checks reachability and row ownership. Since these calls are only reachable from durable outbox dispatch, they are implementation details, not bypasses.

## Residual Risk

No P461 dispatcher direct-call gap remains. Stale observed-wake residue and broad bypass guard remain in P462/P463.
