# Round 002 Gate Criteria

## Gate A - Evidence
- Every DONE task includes executable command, expected output marker, and artifact path.
- Artifact paths in reports must match real files.

## Gate B - Governance
- Teams follow status codes and DoD from `governance/`.
- Incomplete items include blocker owner and `target_round`.

## Gate C - Operability
- At least 2 extracted repo candidates pass startup/health replay checks.
- Critical checks are replayable by non-authors.

## Gate D - Reliability
- Reliability checks (retry/idempotency/timeout/isolation/storage restore) include replay evidence.
- Contract changes include consumer impact note.

## Fail Conditions
- DONE without hard evidence
- Reported artifact path not found
- analysis-only update without shipped change
