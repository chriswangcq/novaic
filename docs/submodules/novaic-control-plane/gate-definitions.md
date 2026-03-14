# Gate Definitions

## Gate A - Execution Evidence
- Every DONE item has command + result + artifact path.

## Gate B - Governance Integrity
- Canonical governance docs are used.
- No mandatory policy is round-only.

## Gate C - Operability
- Critical runbooks are replayable by non-authors.

## Gate D - Reliability
- Reliability checks are scriptable and CI-replayable.

## Fail Conditions
- DONE without evidence
- BLOCKED without dependency owner
- decision-needed item without owner/target_round
