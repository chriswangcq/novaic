## Ticket: CI full matrix 与架构守卫门禁接入

### Problem Definition

Several FSM/worker/cleanup guards now exist as standalone scripts or targeted tests. They must become part of the canonical CI/test matrix so architecture drift cannot pass when only the broad test command or GitHub lint workflow runs.

### Proposed Solution

- Wire the retired runtime vocabulary guard into `.github/workflows/lint.yml`.
- Wire the same guard into the canonical local full-matrix runner `scripts/run_all_tests.sh`.
- Ensure existing FSM/worker architecture guards that protect the new substrate/DSL path are represented in the canonical full-matrix path without relying on memory or manual ad hoc commands.
- Keep dependencies explicit: CI scripts should call named guard commands directly rather than relying on hidden shell state.

### Acceptance Criteria

- `.github/workflows/lint.yml` runs `python3 scripts/ci/lint_retired_runtime_vocabulary.py`.
- `scripts/run_all_tests.sh` runs the root CI/lint guards required to protect the current architecture before package pytest suites.
- The canonical matrix can be run locally and fails on architecture residue.
- No new compatibility bypass or soft-fail path is introduced.

### Verification Plan

- Run all changed shell/Python files through syntax checks.
- Run the newly wired lint commands directly.
- Run the root CI guard subset from `scripts/run_all_tests.sh` that covers the architecture gates.
- Run `python3 /Users/wangchaoqun/.codex/skills/solve-complex-problems/scripts/ledger.py next ...` after recording results.

### Risks

- Full matrix may be expensive; if it is too slow for this ticket, run the deterministic root guard subset plus targeted package tests and leave the complete package matrix to P006 final verification.
- Guard duplication can become noisy; keep direct command list small and clearly owned.

### Assumptions

- GitHub Actions has Python 3 and ripgrep available through the existing lint workflow setup.
- Root-level guard tests and scripts are the intended CI boundary for repo-wide architecture policies.
