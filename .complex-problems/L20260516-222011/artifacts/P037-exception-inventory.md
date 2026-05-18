# Final Direct-Tool Residue Exception Inventory

## Scan Command

```bash
rg -n "\b(im_read|im_reply|im_send|im_history|im_search|im_context|payload_read|payload_search|payload_summarize|payload_qa|subagent_spawn|audio_qa|chat_reply)\b|Use im_read|im_read\(" \
  --glob '!dashboards/*.html' \
  --glob '!docs/roadmap/tickets/**' \
  --glob '!.complex-problems/**' \
  --glob '!*.pyc' \
  .
```

## Classification

| Category | Files | Status |
|---|---|---|
| Migration policy denylist | `novaic-agent-runtime/task_queue/tool_surface_policy.py` | Intentional. These are migrated interface names used to prevent re-entry into direct Runtime executor/schema surfaces. |
| Negative schema/tool guard tests | `novaic-common/tests/test_tool_definitions_contract.py`, `novaic-cortex/tests/test_tool_schemas_limits.py`, `novaic-business/tests/test_pr111_system_prompt_builder.py`, `novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py` | Intentional. These assert old names are absent from prompts, schemas, or active builtin tools. |
| Explicit legacy fixtures | `novaic-agent-runtime/tests/test_pr48_turn_finalizer.py`, `novaic-app/src/components/Visual/ActivityTimeline.test.tsx` | Intentional. Legacy archived direct reply records are explicitly named and tested as legacy/hidden-from-UI behavior. |
| Internal shell-backed API endpoint | `novaic-business/business/internal/environment.py` | Intentional. `environment_im_read` is an internal Environment endpoint behind shell `agentctl im read`, not an LLM tool schema. |
| Prompt forbidden-token guard | `novaic-common/common/contracts/prompt_fragments.py` | Intentional. The old `chat_reply` phrase is listed as forbidden prompt vocabulary. |
| Retired-path lint scripts | `scripts/ci/lint_agent_main_path_acceptance.sh`, `scripts/ci/lint_retired_agent_paths.sh` | Intentional. These scripts scan for old names as forbidden residues. |
| Historical docs / architecture review | `docs/roadmap/agent-perception-action-architecture.md`, `docs/roadmap/agent-root-scope-continuity-design.md`, `docs/cortex/hardening-checklist.md`, `docs/cortex/recall.md`, `docs/cortex/architecture-review-2026-04-17.md` | Intentional/historical. These describe removed behavior or guardrails; not active runtime instructions. |
| Historical Entangled comments/tests | `Entangled/packages/server-python/tests/*`, `Entangled/packages/server-python/entangled/sql/entity_store.py` | Intentional historical root-cause notes for old `chat_reply` symptoms. |

## Unresolved Residue

None found in current active runtime/app/Cortex prompt assembly paths after the targeted cleanup.

## Follow-up Watchpoint

If we later require a zero-grep policy even for negative guard strings, the next step should introduce a shared retired-tool-name registry for guard tests and lint scripts. That is not needed for the current shell-first correctness boundary because the remaining hits are classified and intentional.
