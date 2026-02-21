# Dispatch - Tools Team (Round 007 Findings Fix)

- problem:
  - Tools evidence was flagged for marker/format inconsistency and canonical URL policy mismatch.
- required_solution:
  - Normalize tools report fields to canonical values expected by platform policy.
  - Re-run packaged/dev split replay with explicit `TOOLS_*` and `PASS` markers.
  - Publish closure artifact with no placeholder or parser ambiguity.
- target_state:
  - Tools report has zero format issues.
  - Desktop/Tools format audit reports zero blocking items.
- task: Correct tools `repo_url` and `expected_marker` fields for policy compliance.
- task: Re-run packaged/dev replay and record deterministic marker outputs.
- task: Publish updated closure artifact and pass format self-audit.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-tools-report.md`.
- status: PLANNED
