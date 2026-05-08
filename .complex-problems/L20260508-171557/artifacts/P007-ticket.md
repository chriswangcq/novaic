# T007 CI Bytecode And Generated Artifact Hygiene

## Problem Definition

Python CI guards can generate `__pycache__` and pytest can generate `.pytest_cache`. Those artifacts are gitignored, but they pollute source scans and can make generated-artifact lint fail after a normal verification sequence.

## Proposed Solution

- Make the runtime worker supervision lint avoid bytecode generation internally.
- Set `PYTHONDONTWRITEBYTECODE=1` in the lint workflow.
- Set `PYTHONDONTWRITEBYTECODE=1` in the canonical test runner.
- Add generated artifact cleanup plus `lint_generated_artifacts.sh` to the canonical test runner.
- Add generated artifact lint to the lint workflow so CI catches residue.

## Verification Plan

- Run runtime supervision lint.
- Run generated artifact lint after cleanup.
- Run targeted tests that inspect CI/runtime supervision contracts.

## Acceptance Criteria

- Normal CI/test entrypoints avoid or clean generated Python/test caches.
- Generated artifact lint passes.
- Existing runtime supervision lint still passes.
