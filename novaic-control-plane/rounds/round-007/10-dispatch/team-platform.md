# Dispatch - Platform Team (Round 007 Findings Fix)

- problem:
  - Round 006 audits reported false positives (`team status empty`, malformed `repo_url` extraction), so gate decisions were unreliable.
- required_solution:
  - Fix parser logic for `team status` and `repo_url` extraction.
  - Re-run canonical URL and cross-team audits after all team report updates.
  - Publish reproducible audit commands and outputs.
- target_state:
  - `cross-team-evidence-audit.md` has zero false positives.
  - `canonical-repo-url-audit.md` has zero failures.
  - Audit scripts can be replayed by non-authors with same result.
- task: Implement parser and audit script fixes in `split-fix/repos/novaic-evidence-audit/scripts/`.
- task: Regenerate `split-fix/cross-team-evidence-audit.md` and `split-fix/canonical-repo-url-audit.md`.
- task: Publish regression proof in `split-fix/regression-safety-audit.md`.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-platform-report.md`.
- status: PLANNED
