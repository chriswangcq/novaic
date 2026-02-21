# Dispatch - Runtime Team (Round 004 Code Move)

- task: Migrate remaining lifecycle/state management code from monorepo runtime paths into split runtime repo.
- task: Replace monorepo dependency imports with split-repo-local or shared-package imports and remove dead monorepo references.
- task: Run runtime repo-root startup plus lifecycle contract tests and publish PASS markers with commit evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-runtime-report.md`.
- status: PLANNED
