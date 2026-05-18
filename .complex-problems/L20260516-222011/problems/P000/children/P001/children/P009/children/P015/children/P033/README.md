# Follow-up: classify and isolate remaining direct-tool vocabulary

## Problem

The direct-tool cleanup is not fully closed. A fresh scan still finds `im_read`, `im_reply`, payload direct tools, `audio_qa`, and `subagent_spawn` in current code/tests. Some references are legitimate policy/legacy fixtures, but they are not yet isolated enough to prove that the active shell-first contract is clean.

## Scope

Audit and fix the remaining non-documentation direct-tool references from the latest `P015` scan:

- `novaic-common/tests/test_llm_assembly_contract.py`
- `novaic-common/tests/test_cortex_observation_contract.py`
- `novaic-agent-runtime/task_queue/utils/activity_projection.py`
- `novaic-agent-runtime/tests/test_pr48_turn_finalizer.py`
- `novaic-agent-runtime/tests/test_pr70_explicit_skill_summary_only.py`
- `novaic-agent-runtime/tests/test_pr193_activity_projection.py`
- `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py`
- `novaic-cortex/tests/test_pr67_wake_child_api.py`
- `novaic-cortex/tests/test_tool_schemas_limits.py`
- `novaic-cortex/tests/test_payload_inspection_api.py`
- Policy/API modules that intentionally need migrated tool names.

## Success Criteria

- Current-contract tests use `shell`, `display`, `skill_begin`, `skill_end`, or `sleep` examples unless they are explicitly testing legacy/migration behavior.
- Historical direct-tool fixtures are named as legacy/historical fixtures, not generic active-path examples.
- Runtime activity projection keeps historical readability without presenting legacy direct tools as active executor vocabulary.
- A focused scan report classifies all remaining direct-tool names into one of:
  - migration policy allowlist,
  - legacy historical fixture,
  - internal API endpoint/function,
  - removed.
- Focused unit tests for the touched modules pass.
