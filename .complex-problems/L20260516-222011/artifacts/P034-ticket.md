# Ticket: classify policy and API direct-tool vocabulary

## Problem Definition

Remaining direct-tool tokens in policy/API modules may be legitimate migration/API vocabulary, but they need explicit naming and comments so they cannot be mistaken for active LLM-facing direct executors.

## Proposed Solution

Audit policy/API hits, then minimally adjust names/comments/tests where needed:

- `novaic-agent-runtime/task_queue/tool_surface_policy.py`
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-cortex/novaic_cortex/api.py`
- `novaic-cortex/novaic_cortex/shell_capabilities.py`
- related guard/tests.

## Acceptance Criteria

- Policy names communicate migrated shell capability / final harness target, not active direct surface.
- Internal API function names that must remain are clearly API endpoints, not LLM tools.
- No ordinary comments describe migrated tools as active direct executors.
- Focused py_compile/tests/guard pass.

## Verification Plan

- Focused `rg` over policy/API files.
- Python compile for touched modules.
- Run focused Cortex/runtime tests when touched.

## Risk

Changing API function names could break routes/imports. Prefer comments/constants unless route-level rename is clearly safe.
