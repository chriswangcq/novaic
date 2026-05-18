# Payload direct tool residue scan

## Problem

Search for active direct LLM exposure or stale docs of `payload_read`, `payload_search`, `payload_summarize`, and `payload_qa` outside the intended `cortex payload ...` shell CLI and guard tests.

## Success Criteria

- Active code/tests/docs are searched with `.complex-problems` excluded.
- Valid references inside CLI implementation and absence-guard tests are identified.
- Stale or misleading references are fixed if found.
- Current direct LLM tool schemas remain free of payload tools.
