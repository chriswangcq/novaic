# Round 008 Problem / Solution / Target

## Confirmed open problems from Round 007
- Canonical `repo_url` failures still exist (`local:` scheme in Storage-A/B).
- Audit output and final report submission timing can drift, causing stale decisions.
- Teams still need a formal channel to raise ambiguity before next-round redispatch.

## Non-negotiable requirements
- `repo_url` must be exactly one of:
  - `https://github.com/<org>/<repo>`
  - `file:///absolute/path/to/<repo-root>` (not ending with `/repos`)
- Audit scripts must run after the last report edit and include timestamp.
- Reports must include `questions_for_program_owner` section with structured items.
- Every team must deliver:
  - one code/behavior hardening change,
  - one failure-path verification,
  - one operability artifact for non-author replay.
- Every report must satisfy machine-readable contract in `20-reports/README.md`.

## Why previous execution drifted
- Teams interpreted field formats differently (`repo_url`, multi-line command blocks, marker placement).
- Audit scripts and report syntax were not tightly coupled.
- Result: people considered tasks done while gate parser could not verify them.

## This round execution rule
- Human-readable text is not enough; parser-readable fields are the source of truth.
- If parser fields fail contract, task is treated as not done regardless of narrative summary.

## Target state for round close
- `canonical-repo-url-audit.md`: zero failures.
- `cross-team-evidence-audit.md`: zero false positives and timestamp >= latest report update.
- `desktop-tools-closure-format-audit.md`: zero blocking issues.
- Each report includes:
  - `problem_fixed`
  - `solution_applied`
  - `target_state_proof`
  - `questions_for_program_owner`
