# Round 011 Gate Criteria

## Gate A - Canonical URL and Parser Contract
- `repo_url` uses one of the 7 approved `https://github.com/chriswangcq/<repo>` URLs only.
- Required fields remain machine-readable: command + expected_marker + repo_url + commit_sha + migrated_paths + artifact_path.

## Gate B - Full Remote Commit Verification
- `check_commit_reachability.py` uses SSH `git ls-remote` (not local-clone oracle).
- No `UNREACHABLE` commit pairs (remote reachable but SHA absent from refs).
- At least one `REACHABLE` pair per team.
- `SKIP_REMOTE` allowed only when SSH itself fails (returncode != 0); count should be 0 for all repos under normal network conditions.

## Gate C - Cross-Team Evidence Quality
- findings_count = 0 in cross-team audit.
- All 6 required evidence fields present and non-placeholder per team.

## Gate D - Regression Safety
- Teams green in round-010 must not regress on canonical URL or status.

## Gate E - Negative Fixture Proof
- Negative fixture with a valid-format SHA that is NOT a ref tip in the remote must produce UNREACHABLE (not SKIP_REMOTE).

## Fail Conditions
- Any non-https repo_url in reports.
- Any `UNREACHABLE` commit pair in team reports.
- `REACHABLE` count = 0 for any team.
- Negative fixture test does not detect UNREACHABLE.
- SKIP_REMOTE for repos where SSH is reachable.
