# Step result projection contract audit

## Problem

Step result projection is the boundary where raw tool output becomes LLM-visible history/current context. It must enforce terminal-style shell text, manifest-only historical artifacts, current-round display behavior, and no accidental inline large payloads.

## Success Criteria

- `step_result_projection` behavior is audited for shell, display, payload, blob artifact, and generic tool outputs.
- Historical display/tool results are proven to be manifest-only and do not reintroduce base64/image bytes.
- Current-round display behavior is proven to be provider-usable without polluting future history.
- Any active projection branch that emits raw base64 or unbounded tool text into text context is fixed.
- Regression tests cover shell bounded text, display current projection, display historical projection, and payload manifest behavior.
