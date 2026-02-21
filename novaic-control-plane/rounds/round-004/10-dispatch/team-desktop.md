# Dispatch - Desktop Team (Round 004 Code Move)

- task: Refactor desktop runtime startup to default to split-service endpoint resolution in non-dev mode, removing monorepo-only fallback assumptions.
- task: Replace hardcoded internal API paths in desktop command/service modules with configurable split-service base URLs.
- task: Run desktop startup against split services and publish one end-to-end PASS marker with commit evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-desktop-report.md`.
- status: PLANNED
