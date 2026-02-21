# Dispatch - API Team (Round 004 Code Move)

- task: Continue gateway extraction by moving remaining runtime-forwarding and health route code from monorepo gateway module into split gateway repo.
- task: Update gateway service wiring to consume split runtime repo endpoint/config, not monorepo internal shortcuts.
- task: Run gateway repo-root startup and one end-to-end call path to runtime, with PASS markers and commit evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-api-report.md`.
- status: PLANNED
