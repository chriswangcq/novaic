# Dispatch - Storage-A/B Team (Round 003 Real Split)

- task: Split storage domains into two independent repo candidates and push first split commits.
- task: Publish `split-move/storage-ab-migration-map.md` with A/B source->target path mapping and schema ownership split.
- task: Run one restore/smoke path per domain from split candidate roots and record PASS markers.
- evidence: for each DONE item provide command + expected_marker + repo_url + commit_sha + migrated_paths + artifact_path in `20-reports/team-storage-ab-report.md`.
- status: PLANNED
