# VMuse contract tests after cleanup

## Problem
Ensure VMuse tests prove the current tool-output/blob contract and do not keep deleted FastMCP/direct-media behavior alive.

## Success Criteria
- Focused VMuse tests pass after source cleanup.
- Tests or contract markers fail on stale FastMCP direct-media reintroduction.
- Verification evidence distinguishes allowed internal base64 transport from forbidden direct LLM media return paths.
