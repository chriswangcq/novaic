# Final Old Authority Cleanup Verification

## Problem

After source, guardrail, and doc cleanup, the repository needs a final proof pass. Without it, old paths may remain hidden in tests/docs or a cleanup may break behavior.

## Success Criteria

- Full Cortex tests pass.
- LogicalFS tests pass.
- Sandbox-service tests pass.
- Residue scans for old authority names, old direct constructors, old module imports, and stale canonical docs pass or only show explicitly historical roadmap text.
- P024 can be checked without unclosed follow-up.
