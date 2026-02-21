# Dispatch - Storage-A/B Team (Round 004 Code Move)

- task: Move remaining file-service and tool-result-service domain code from monorepo into split storage-a/storage-b repos.
- task: Replace monorepo cross-imports with API-based integration between storage-a and storage-b where needed.
- task: Run smoke/restore from both split repo roots and one cross-repo chain replay, then publish PASS markers with commit evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-storage-ab-report.md`.
- status: PLANNED
