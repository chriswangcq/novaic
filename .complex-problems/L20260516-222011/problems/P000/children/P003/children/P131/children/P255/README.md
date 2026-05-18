# Runtime large-output boundary sweep

## Problem
Audit runtime shell/tool result handling for large stdout/stderr, unstructured executor dumps, durable raw payload separation, and monitor/public projection truncation.

## Success Criteria
- Runtime large-output clusters are cited and classified.
- Shell LLM-visible output is bounded while raw stdout/stderr is durable/pointer-accessible.
- Unstructured executor result paths sanitize media bytes and avoid unbounded context flooding.
