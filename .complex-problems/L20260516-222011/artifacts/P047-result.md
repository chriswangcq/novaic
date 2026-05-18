# Result: Ephemeral Cortex Backing Path Residue Scan

## Summary

The focused scan for ephemeral Cortex backing path residue found no active guidance or runtime path that asks agents to reuse `/tmp/novaic-cortex-sandbox-*` paths. Remaining `novaic-cortex-sandbox-*` references are limited to guardrails, tests, or historical/design documentation that warns against using ephemeral backing paths.

## Done

- Verified current stable path guidance is expressed through `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW`.
- Classified remaining `novaic-cortex-sandbox-*` references:
  - `novaic-common/common/tools/llm_builtin.py` contains shell tool guidance warning not to copy or reuse backing paths.
  - `novaic-cortex/novaic_cortex/sandbox.py` contains the shell guard/error path that rejects direct backing-path usage.
  - `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` and `novaic-cortex/tests/test_tool_schemas_limits.py` cover the guard behavior and schema wording.
  - `docs/cortex/sandbox-shell.md` and `docs/cortex/state-authority-implementation-plan.md` retain historical/design context rather than current execution guidance.

## Verification

- Focused repository scan for `/cortex/ro`, `/cortex/rw`, `$RO`, `$RW`, and `novaic-cortex-sandbox-*` residue.
- Checked that ephemeral backing path references are either explicit prohibitions, tests for the prohibition, or non-runtime documentation.
- No active shell examples were found that instruct agents to paste an old `/tmp/novaic-cortex-sandbox-*` path into later shell commands.

## Known Gaps

- None for this ticket. Broader media and tool-output contract cleanup is intentionally handled by sibling problems `P048` and `P049`.

## Artifacts

- This result file: `.complex-problems/L20260516-222011/artifacts/P047-result.md`
