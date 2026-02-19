# Round 005 Gate Criteria (No-Tech-Debt)

## Gate A - Reproducible Engineering
- Every DONE item has runnable command evidence.
- At least one replay run is attached for each critical path.

## Gate B - Contract Governance
- Storage contracts under `contracts/` have explicit versioning and ownership rule.
- Breaking-change approval workflow is documented and enforced by checklist.

## Gate C - Operability Hardening
- Desktop validation has scripted fresh-profile and clean-machine-equivalent steps.
- Runtime startup safeguards are CI-enforced, not convention-only.

## Gate D - Reliability Hardening
- Agent Runtime idempotency/retry checks include stress replay.
- Tools reliability checks include prerequisite validation and replay evidence.

## Fail Conditions
- Mandatory decision-needed item has no owner or deadline.
- Claimed DONE item missing evidence.
- Critical guardrail exists only in docs but not in CI/script enforcement.
