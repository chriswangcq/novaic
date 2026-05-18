# Sandbox Backing Path Residue Audit Result

## Summary

Completed the sandbox backing path residue audit. No active contract tells agents to reuse `/tmp/novaic-cortex-sandbox-*`; remaining references are defensive rejection logic, tests for that guard, or builtin tool descriptions telling agents to use stable `/cortex/ro` and `/cortex/rw` instead.

## Scans

- `.complex-problems/L20260516-222011/tmp/P647-sandbox-path-scan.txt` records scans for ephemeral backing paths and stable path contract terms.
- `.complex-problems/L20260516-222011/tmp/P647-sandbox-path-context.txt` records line context for meaningful hits.

## Classification

- Defensive runtime guard:
  - `novaic-cortex/novaic_cortex/sandbox.py:31-50` rejects commands containing `novaic-cortex-sandbox-*` and tells agents to use `/cortex/ro`, `/cortex/rw`, `$RO`, or `$RW`.
- Guard tests:
  - `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py:29-66` verifies ephemeral backing paths are rejected before execution, including quoted occurrences.
  - `novaic-cortex/tests/test_tool_schemas_limits.py` and `novaic-common/tests/test_tool_definitions_contract.py` verify the tool description warns against backing paths.
- Stable contract text:
  - `novaic-common/common/tools/llm_builtin.py:16-22` and `novaic-cortex/novaic_cortex/shell_capabilities.py:104-106` explicitly direct agents to stable `/cortex/ro` and `/cortex/rw`.
- Intended stable path tests:
  - Sandbox service, LogicalFS, Cortex, and runtime tests reference `/cortex/ro`/`/cortex/rw` as the stable public contract.

## Follow-Up Decision

No follow-up required. Remaining ephemeral backing path strings are defensive and test-only; there is no active path leak that presents `/tmp/novaic-cortex-sandbox-*` as a reusable shell contract.
