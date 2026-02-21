# Round 009 Charter

## Window
- Round ID: round-009
- Round status: ACTIVE
- Cadence: sync and submission happen within the round

## Objective
Move repo evidence from local-path trust to remote-traceable trust:
enforce `https://github.com/<org>/<repo>` as the only accepted `repo_url` format
and verify that every reported `commit_sha` is reachable in the referenced remote.

## Scope
- Upgrade audit scripts: https-only `repo_url` enforcement + commit reachability check
- Negative fixtures proving audit rejects invalid URL and unreachable SHA
- One-command gate runner (`gate_round009.sh`)
- All team reports use `https://github.com/` `repo_url` values

## Success Criteria
- `canonical-repo-url-audit.md`: zero failures (https-only policy)
- `commit-reachability-audit.md`: zero reachability failures
- `cross-team-evidence-audit.md`: zero findings, zero false positives
- Negative fixtures prove both rejection paths with deterministic markers
- `ROUND009_GATE_RUNNER_PASS` printed by `gate_round009.sh`
