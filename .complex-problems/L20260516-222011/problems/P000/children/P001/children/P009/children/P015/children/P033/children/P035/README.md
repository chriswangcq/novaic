# Child Problem: test fixture vocabulary cleanup

## Problem

Several tests still use direct-tool names as generic examples. Some are valid legacy regression tests, but current-contract tests should use final harness tools or shell-first examples.

## Success Criteria

- Replace generic current-contract fixtures using `im_read`, `im_reply`, payload tools, `audio_qa`, or `subagent_spawn`.
- Rename unavoidable legacy fixtures/helpers to make legacy intent explicit.
- Preserve regression coverage for old archived step data.
- Run focused test files for changed tests.
