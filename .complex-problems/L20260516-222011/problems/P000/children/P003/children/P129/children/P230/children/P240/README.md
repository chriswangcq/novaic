# Audit shell capability guidance for payload and output boundaries

## Problem

Shell capability help and CLI guidance must teach bounded terminal output, explicit payload read/search/summarize/qa commands, and artifact/display usage without encouraging agents to paste raw large outputs or base64 into replies/context.

This belongs under `P230` because most interface tools now live inside shell, so CLI guidance is the practical contract the agent sees.

## Success Criteria

- `shell_capabilities.py` payload/help text is mapped with file/function pointers.
- Guidance clearly points to explicit `cortex payload ...` commands for full payload inspection.
- Focused shell capability and output contract tests pass.
- Any stale or misleading wording found is corrected.
