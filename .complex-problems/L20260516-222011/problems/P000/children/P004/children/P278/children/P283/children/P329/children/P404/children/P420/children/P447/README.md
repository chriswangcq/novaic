# Cortex media payload and projection compatibility guard

## Problem

Final Cortex verification needs a focused guard for shell/display/tool-result/payload projection boundaries, especially raw base64 or large payloads entering LLM history as text.

## Success Criteria

- Save source guard scans for `_mcp_content`, base64/media payload markers, shell artifact contracts, step-result projection, and payload readback.
- Classify remaining hits as shell text manifest, display perception path, bounded payload inspection, tests/fixtures, or unresolved risk.
- Confirm shell/agent-facing behavior remains pointer-oriented and does not expose raw screenshot/file payloads as ordinary context text.
- Confirm display perception remains shell-outside and does not poison historical context.
