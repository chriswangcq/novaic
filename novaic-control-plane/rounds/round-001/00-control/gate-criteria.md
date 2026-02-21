# Round 001 Gate Criteria

## Gate A - Evidence
- Every DONE task includes executable command output and changed file path evidence.

## Gate B - Governance
- Teams use status codes and DoD from `governance/`.
- Reports include explicit `target_round` for incomplete work.

## Gate C - Operability
- Critical split checks are replayable by non-authors (build/test/import checks).

## Gate D - Reliability
- Reliability-related teams provide replay evidence, not only prose.
- Any cross-repo contract change must include consumer impact note.

## Fail Conditions
- DONE without implementation evidence
- Report missing required sections
- "Understood/Investigated" statements without shipped change or executable proof
