# IM direct tool residue scan

## Problem

Search for active direct LLM exposure or stale documentation of `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, or `im_context` outside the intended `agentctl im ...` shell CLI and guard tests.

## Success Criteria

- Active code/tests/docs are searched with `.complex-problems` excluded.
- Valid references inside CLI implementation and absence-guard tests are identified.
- Stale or misleading references are fixed if found.
- Current direct LLM tool schemas remain free of IM tools.
