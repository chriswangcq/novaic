# Verify Hygiene And Ledger Closure

## Problem Definition

The post-deploy audit must end with clean repository hygiene evidence: tests/lints pass, generated artifacts are cleaned, the audit ledger validates/renders, and git status is understood.

## Proposed Solution

Run the targeted runtime test suite, runtime supervision lint, generated-artifact lint, audit ledger render/validate/status, and final git status checks. Clean generated Python artifacts before the final generated-artifact lint.

## Acceptance Criteria

- Relevant targeted runtime tests pass.
- Runtime supervision lint passes.
- Generated artifact lint passes after cleanup.
- The new audit ledger validates and renders.
- Git status contains only intentional audit ledger changes after the audit, or is clean after committing them.

## Verification Plan

- Run the targeted runtime/FSM/DSL suite.
- Run `lint_runtime_worker_supervision.py`.
- Remove Python cache artifacts and run `lint_generated_artifacts.sh`.
- Run `ledger.py render`, `validate`, `status`, and `next` for the audit ledger.
- Run parent and submodule `git status --short`.

## Risks

- Running tests creates cache files; cleanup must happen before final generated-artifact lint.

## Assumptions

- The targeted runtime/FSM/DSL suite is the appropriate nearest project-wide check for this touched surface.
