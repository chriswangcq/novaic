# Dispatch - Platform Team (Round 009 Real Remote Cutover)

- problem:
  - Round 008 proved local evidence quality, but repo proof still accepts local-only references and does not verify remote commit reachability.
- required_solution:
  - Move audit baseline from local-path trust to remote-traceable trust.
  - Enforce `repo_url` as `https://github.com/<org>/<repo>` for Round 009 reports.
  - Add commit reachability checks so fake SHA / wrong repo combinations fail deterministically.
- target_state:
  - Round 009 audits reject non-https repo URLs.
  - Round 009 audits reject unreachable commit SHAs.
  - One-command gate runner provides final PASS/FAIL outcome.
- task (code/behavior): Upgrade audit scripts to enforce `https://github.com/...` `repo_url` format and verify `commit_sha` exists in referenced remote repo.
- task (failure-path): Add negative fixtures for `(a) invalid github repo_url`, `(b) unreachable commit_sha`, and prove audits fail with deterministic markers for each.
- task (operability): Publish `gate_round009.sh` that runs canonical URL audit, evidence audit, and regression audit in sequence, exiting non-zero on first failure.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-platform-report.md`.
- status: PLANNED
