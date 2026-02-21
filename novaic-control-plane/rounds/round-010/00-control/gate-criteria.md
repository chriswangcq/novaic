# Round 010 Gate Criteria

## Gate A - Canonical URL and Parser Contract
- `repo_url` uses `https://github.com/<org>/<repo>` only.
- Required fields remain machine-readable and executable as-is.

## Gate B - Commit Reachability Quality
- No `UNREACHABLE` commit pairs.
- At least one `REACHABLE` commit pair exists per team.
- `SKIP_REMOTE` is allowed only as residual, not 100% of pairs.

## Gate C - Operability from Clean Clone
- Each team provides one non-author replay path that starts from remote clone/setup.
- Operability artifact includes command + expected marker + artifact path.

## Gate D - Round Closure Reliability
- Gate runner exits non-zero on first failure and prints final PASS marker on success.
- Round feedback and close retro must be populated (no template placeholders).

## Fail Conditions
- Any non-https repo_url in reports.
- Any `UNREACHABLE` commit pair.
- `REACHABLE` count equals zero for any team.
- Missing non-author remote replay evidence.
