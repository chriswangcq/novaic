# Dispatch - Platform Team (Round 004 Code Move)

- task: Migrate shared/common runtime modules that are duplicated across split repos into one shared package and update imports in split repos.
- task: Remove monorepo-only path assumptions from startup scripts used by split repos.
- task: Run one multi-repo bring-up command that starts gateway + runtime + tools via split repos and record PASS marker.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-platform-report.md`.
- status: PLANNED
