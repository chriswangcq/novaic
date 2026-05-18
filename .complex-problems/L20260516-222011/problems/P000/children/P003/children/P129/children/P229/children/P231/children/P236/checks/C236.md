# Check: runtime tool handler durable payload handoff is solved

## Summary

`P236` is solved by `R222`, backed by child results `R220` and `R221`. The runtime handoff boundary is verified for both heavy-output classes in scope: shell output and display/media output.

## Evidence

- `R220`/`C234` prove shell public output is bounded terminal text and raw stdout/stderr live in durable payload.
- `R221`/`C235` prove display/media image data is gated through `display_perception` and historical/default tool text uses placeholders rather than raw base64.
- Focused tests passed across both branches: shell tests `19 passed`, display/media tests `14 passed`.

## Criteria Map

- Runtime tool handler/bridge code paths for shell and display-like outputs are mapped with file/function pointers: satisfied by child results mapping `tool_handlers.py`, `step_result_client.py`, `context.py`, and `multimodal.py`.
- Evidence shows heavy raw output is separated from public compact projection and carried as durable payload input where applicable: satisfied by shell durable payload and display placeholder/current-perception gating evidence.
- Focused runtime tests pass for shell/display projection and no raw base64/large stdout in normal tool messages: satisfied by the two child test suites.

## Execution Map

- Split ticket `T225` produced child problems `P237` and `P238`.
- `P237` closed with `R220` and check `C234`.
- `P238` closed with `R221` and check `C235`.
- Parent result `R222` summarizes those closed child outcomes.

## Stress Test

The parent-level stress case is mixed history: a shell command emits base64-like text and a display tool emits image `_mcp_content`; later LLM context assembly should receive compact shell text and only current display perception as image. The two child checks cover each half with regression-focused tests, including media-like shell stdout and historical display image injection.

## Residual Risk

Non-blocking for `P236`: CLI-specific artifact manifest quality and schema/tool guidance remain under `P230`; Cortex persistence is separately closed under `P235`.

## Result IDs

- `R222`
- `R220`
- `R221`
