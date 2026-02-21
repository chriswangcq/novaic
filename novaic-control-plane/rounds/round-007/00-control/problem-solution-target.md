# Round 007 Problem / Solution / Target

## Why previous rounds did not close
- Problem definition was not explicit enough at task level, so teams optimized for local pass markers instead of gate-level closure.
- Evidence audit scripts had parsing flaws, causing false positives and confusing teams on real vs fake failures.
- Canonical `repo_url` policy was interpreted differently (`file:///`, `local:`, ssh/https), so reports diverged.

## Round 007 must-fix problems
- P1-1: Canonical `repo_url` failures are not zero.
- P1-2: Audit outputs are not fully trustworthy (false positives still appear).
- P1-3: Desktop/Tools evidence marker format is not consistently machine-checkable.

## Required solution pattern (for every team)
- State exact problem in report task block.
- Apply concrete fix and include code/config/report diff evidence.
- Prove target state with replay command and deterministic PASS marker.

## Target state required for round close
- `canonical-repo-url-audit.md`: zero failures.
- `cross-team-evidence-audit.md`: zero false positives and reproducible output.
- `desktop-tools-closure-format-audit.md`: zero blocking issues.
- All team reports: no placeholders, canonical `repo_url`, real `commit_sha`, explicit marker list.
