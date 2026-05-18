# Check: combined large shell/display projection boundary holds

## Summary

`P234` is solved by `R226`. The combined regression surface has code and test evidence: shell emits bounded terminal text, display images use current perception image channels only, and historical/default context expansion does not inject raw image/base64 text.

## Evidence

- `R220`/`C234`: shell large/media-like stdout stays bounded and durable-payload backed.
- `R221`/`C235`: display image content is placeholdered in tool text and only current display perception creates structured image messages.
- `R225`/`C239`: default runtime context expansion uses formatted step projection and avoids full payload reads.
- Combined tests passed: `29 passed in 0.10s`.
- Search found `raw_shell_result` only in absence assertions and `data:image` only in intended multimodal conversion/test paths.

## Criteria Map

- Shell result projection and display/media result projection paths are mapped to compact/default behavior: satisfied by supporting child results and combined search.
- Raw base64/large stdout is not normal history text by default: satisfied by shell media-like stdout test, display history injection tests, and context expansion tests.
- Combined focused tests pass: satisfied by 29-test combined run.

## Execution Map

- Ticket `T230` ran a bounded combined regression audit.
- Execution searched suspicious patterns, ran combined focused tests, and recorded `R226`.

## Stress Test

The combined stress case is a session containing both a shell command that prints image-like base64 and a display tool result with image content. The relevant tests cover both cases: shell output remains terminal text without `_mcp_content` or `data:image/`, and display history only converts to image content when marked as current `display_perception`.

## Residual Risk

Non-blocking for `P234`: CLI-by-CLI manifest adherence is handled by `P230`.

## Result IDs

- `R226`
- `R220`
- `R221`
- `R225`
