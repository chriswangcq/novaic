# Dispatch - Desktop Team (Round 009 Real Remote Cutover)

- problem:
  - Desktop split mode still risks partial startup under misconfiguration; remote multi-service dependency validation must be strict for production packaging.
- required_solution:
  - Enforce explicit split dependency config in desktop startup path.
  - Prove tools-hop failure is surfaced deterministically to diagnostics.
  - Provide a complete non-author closure bundle for split desktop chain.
- target_state:
  - Desktop split startup fails fast (or policy-defined strict handling) on missing mandatory external service config.
  - Tools-hop outage replay emits stable failure marker and diagnostics artifact.
  - Closure bundle documents happy/failure paths and troubleshooting matrix.
- task (code/behavior): Strengthen split-config validation to remove remaining implicit fallback behavior and enforce explicit external dependency endpoints.
- task (failure-path): Replay tools endpoint unavailable scenario and verify deterministic `TOOLS_HOP=FAIL` marker plus diagnostics output for non-author verification.
- task (operability): Publish `desktop-closure-bundle-round009.md` with 3-hop checks, split-config validation replay, marker index, and troubleshooting table.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-desktop-report.md`.
- status: PLANNED
