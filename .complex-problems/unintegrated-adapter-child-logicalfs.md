# Audit Cortex LogicalFS and Sandbox adapter cutover

## Problem

Find any remaining live code paths where Cortex/Sandbox/LogicalFS still bypass the intended lightweight LogicalFS adapter model, especially broad `/ro` materialization, direct Blob/Workspace filesystem reads inside shell paths, old fallback mounts, or local execution fallback.

## Success Criteria

- Search and inspect LogicalFS, Sandbox, sandboxd, Workspace, and shell execution paths.
- Confirm whether any broad recursive materialization remains on shell/live execution paths.
- Separate runtime code findings from docs/tests.
- Record exact file/function evidence and any needed follow-up.
