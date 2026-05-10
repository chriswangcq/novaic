# Add runtime tool surface inventory and guard tests

## Problem Definition

The Runtime currently exposes many direct harness tools through `_EXECUTORS`. Before migrating them into shell capabilities, every tool must have an explicit target classification so future phases cannot accidentally add or keep direct tools without review.

## Proposed Solution

Add a small runtime policy module that classifies the current tool surface into:

- final harness primitives;
- shell-migration candidates;
- structural lifecycle tools;
- optional notes for high-risk output producers.

Add tests that import `_EXECUTORS` and verify every executor is classified, final harness primitives are exactly the intended set, and all non-final direct tools are explicitly marked for shell migration.

## Acceptance Criteria

- A code-level inventory exists in `novaic-agent-runtime`.
- Tests fail if `_EXECUTORS` gains an unclassified tool.
- Tests document that final harness primitives are exactly `shell`, `display`, `skill_begin`, `skill_end`, `sleep`.
- Tests document that direct `im_*`, `subagent_spawn`, `payload_*`, `audio_qa`, and `hd_*` are migration candidates.
- Existing runtime behavior is not removed in this phase.

## Verification Plan

- Run the new test file.
- Run nearby runtime tool path / prompt contract tests.
- Review git diff for scope.

## Risks

- Importing `_EXECUTORS` in tests may trigger dependencies; keep tests lightweight and import-only.
- Current dirty worktree already has modified Runtime files; avoid editing those unless necessary.

## Assumptions

- Phase 0 is additive guardrail work, not behavioral cutover.
- Future phases will turn these guardrails from inventory checks into deletion/cutover hard gates.
