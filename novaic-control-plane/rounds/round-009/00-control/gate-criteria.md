# Round 009 Gate Criteria

## Gate A - https-Only Canonical URL
- `canonical-repo-url-audit.md` reports zero failures.
- Only `https://github.com/<org>/<repo>` (exactly 5 path segments) accepted.
- `file:///` and `local:` schemes both rejected.

## Gate B - Commit Reachability
- `commit-reachability-audit.md` reports zero reachability failures.
- Every `commit_sha` that can be checked against its `repo_url` remote returns reachable.
- Repos unreachable due to network/offline receive `SKIP_REMOTE` status (not FAIL).

## Gate C - Evidence and Marker Quality
- Required PASS markers are explicit and machine-greppable.
- No template placeholders in any required field.
- Each team has one failure-path replay with deterministic marker.
- Negative fixture tests prove audit scripts reject bad inputs.

## Gate D - Communication and Operability
- Every report has `questions_for_program_owner` section.
- Each report includes one operability artifact path.
- `gate_round009.sh` exits non-zero on any audit failure.

## Fail Conditions
- Any `file:///` or `local:` `repo_url` in any report => Gate A fail
- Any confirmed-unreachable `commit_sha` (not SKIP_REMOTE) => Gate B fail
- Missing `questions_for_program_owner` section => Gate D fail
- Negative fixtures not present or not passing => Gate C fail
