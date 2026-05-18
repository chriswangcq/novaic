# Direct tool and hidden harness residue scan

## Problem

Search active code/tests/docs for old direct LLM tools that should now be shell CLI capabilities, such as `im_reply`, `payload_read`, `subagent_spawn`, and `audio_qa`, and distinguish current intended references from stale residue.

## Success Criteria

- Active code and current tests are searched with bounded output.
- Current tool schema contract is not contradicted by stale references.
- Any active direct-tool exposure or misleading docs are fixed or routed.
- Historical ledger hits are excluded or labeled as historical.
