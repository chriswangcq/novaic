# P818 Check: Wire Factory Log Renderers To Safe Projection

## Verdict

`success`

## Summary

The factory log renderers now use the projection helper on the scoped raw payload paths. The check executed renderer output against representative base64-like message, reasoning, tool argument, raw request/response, visual detail, and BlobRef samples.

## Criteria Map

- Raw request and response tabs use projected output: satisfied by `renderRawDetail` using `projectedBodyText`.
- Message content/reasoning and tool-call arguments use projected output: satisfied by `renderMessageBubble` using `projectedText` / `projectedJson`.
- Visual fallback bodies and `x_factory` use projected output: satisfied by `renderVisualDetail` changes.
- Remaining `JSON.stringify` calls are safe or projection-related: satisfied by focused `rg` classification.
- Edited HTML/JS passes focused checks: satisfied by `git diff --check` and Node renderer extraction test.

## Evidence

- Result `R798`.
- `git -C novaic-llm-factory diff --check -- static/factory-logs.html`: passed.
- Node renderer extraction test printed `factory_log_renderer_projection_ok`.
- Focused `rg` for `JSON.stringify`, raw body variables, reasoning/content, and projected helpers shows remaining raw body uses flow through `projectedBodyText`.

## Stress Test

Because this was one-go renderer wiring, the check looked for two failure modes: raw base64 leaking through rendered HTML and BlobRefs being over-redacted. The renderer sample would fail if raw base64 survived in message, tool argument, raw tab, or visual detail HTML, and it also asserted BlobRef preservation.

## Residual Risk

No P818-scoped residual risk remains. P819 still owns aggregate verification for the broader factory-log projection scope.
