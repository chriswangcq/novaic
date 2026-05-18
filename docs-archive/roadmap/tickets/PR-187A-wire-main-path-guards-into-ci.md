# PR-187A — Wire Main-Path Guards Into CI and Root Test Entrypoint

Status: `[closed]` — 2026-05-03

## Goal

Make the PR-186 main-path acceptance guard part of the normal machine-checked path instead of relying on manual closure discipline.

## Current-State Analysis

Before this ticket:

- `.github/workflows/lint.yml` did not invoke the PR-186 main-path guard bundle.
- `.github/workflows/lint.yml` invoked `scripts/ci/lint_outbox_trigger_sync.sh`, which no longer existed.
- `scripts/run_all_tests.sh` only ran selected repository pytest suites and skipped root guardrails.

## Implementation

- [x] Remove the missing `lint_outbox_trigger_sync.sh` workflow step.
- [x] Add GitHub lint steps for:
  - `scripts/ci/lint_agent_main_path_acceptance.sh`
  - `scripts/ci/lint_retired_agent_paths.sh`
  - `scripts/ci/lint_lifecycle_loop_ownership.sh`
- [x] Add the same guard bundle to `scripts/run_all_tests.sh`.
- [x] Keep the change as guard/test wiring only; no runtime behavior change.

## Validation

```bash
scripts/ci/lint_agent_main_path_acceptance.sh
scripts/ci/lint_retired_agent_paths.sh
scripts/ci/lint_lifecycle_loop_ownership.sh
scripts/run_all_tests.sh
rg -n "lint_outbox_trigger_sync" .github/workflows scripts
```

Result: all passed; no retired workflow reference remains.
