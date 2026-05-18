# Payload API and pointer retrieval boundary audit

## Problem

Payload APIs are the intended way to inspect large outputs after context externalization. The boundary is only sound if full payload reads/search/summaries stay explicit, bounded, and pointer-addressed, while normal context assembly keeps only references and compact projections.

## Success Criteria

- Cortex payload read/search/summarize/qa APIs are mapped and verified against pointer-oriented expectations.
- Tool/step writes store large outputs through payload references rather than inline context entries.
- Payload reads are bounded or explicit, and no default LLM context path silently uses full payload reads.
- CLI/tool schema guidance points agents to explicit payload inspection instead of expecting inline history.
- Tests cover payload reference availability and bounded retrieval behavior.
