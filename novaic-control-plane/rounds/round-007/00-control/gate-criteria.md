# Round 007 Gate Criteria

## Gate A - Canonical URL Compliance
- All `repo_url` fields pass canonical policy.
- No ambiguous directory-level or placeholder URLs.

## Gate B - Audit Correctness
- Cross-team audit output matches current report states.
- No false positives for team status or replayable command checks.

## Gate C - Desktop/Tools Evidence Closure
- Desktop and Tools format audit has no blocking issue.
- Packaged/dev split markers remain replayable.

## Gate D - Regression Safety
- API/Runtime/Agent/Storage split chains remain green after evidence fixes.

## Fail Conditions
- canonical URL failures remain
- stale or incorrect audit artifacts
- template placeholders still present in reports
