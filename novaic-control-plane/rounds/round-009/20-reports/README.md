# Reports

Each team report must include:
- `problem_fixed`
- `solution_applied`
- `target_state_proof`
- one `code/behavior` change evidence
- one `failure-path` replay evidence
- one `operability artifact` reference
- command + expected marker
- canonical `repo_url` (https://github.com/<org>/<repo> ONLY)
- `commit_sha` + `migrated_paths`
- artifact paths
- `questions_for_program_owner` (required section; can be empty)

## Machine-readable contract (mandatory)
- `repo_url` must be `https://github.com/<org>/<repo>` exactly (5 path segments, no trailing slash).
- `file:///` and `local:` schemes are rejected in Round 009.
- `command` must be executable as-is (no ellipsis, no placeholder text).
- `expected_marker` must be literal strings that appear in command output or artifact.
- `commit_sha` must be full 40-char SHA (no `PENDING`, no short hash).
- `status` must be one literal value: `PLANNED` | `IN_PROGRESS` | `BLOCKED` | `DONE` | `DONE_WITH_GAPS`.

## Required field shape (example)
- `repo_url: \`https://github.com/myorg/myrepo\``
- `command: \`bash scripts/replay.sh\``
- `expected_marker: \`REPLAY_PASS\``
- `commit_sha: \`0123456789abcdef0123456789abcdef01234567\``
- `artifact_path: \`rounds/round-009/split-close/example.md\``

## Rejection rules
- Any `repo_url` that is not `https://github.com/<org>/<repo>` => reject.
- Any placeholder text (`...`, `PENDING`, template enums) in required fields => reject.
- Any `command` that cannot run directly => reject.

## questions_for_program_owner format
- question:
- why_blocking:
- options:
- recommended_option:
- impact_if_unanswered:
- requested_by_round:
