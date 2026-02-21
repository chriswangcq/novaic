# Dispatch - Tools Team (Round 004 Code Move)

- task: Migrate remaining tools execution/policy code from monorepo tools paths into split tools repo.
- task: Update callers to consume split tools service endpoints/imports instead of monorepo-local module paths.
- task: Run timeout/isolation tests from split tools repo root and publish PASS markers with commit evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-tools-report.md`.
- status: PLANNED
