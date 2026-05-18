# App shell artifact output UI contract discovery result

## Summary

Shell artifact output UI discovery is complete across Chat, Monitor, and BlobRef/artifact preview surfaces. Active Chat messages, Monitor activity records, and BlobRef previews are aligned with the terminal-text plus BlobRef/artifact-reference contract. One cleanup candidate remains: `AssistantMessage.tsx` contains legacy event rendering that can stringify object content and render event-provided image URLs even though active Entangled messages do not populate events.

## Done

- Closed `P779` / `R760`: Chat shell output rendering discovery.
- Closed `P780` / `R761`: Monitor shell artifact projection discovery.
- Closed `P781` / `R762`: BlobRef and artifact preview contract discovery.

## Verification

- `R760` shows active Chat message conversion uses canonical `{text, attachments}` envelopes and BlobRef-backed attachments; focused chat tests passed. It also found the `AssistantMessage.tsx` legacy event-rendering cleanup candidate.
- `R761` shows Monitor projection allowlists activity fields, hides raw payload-like details, and passes focused ActivityTimeline tests.
- `R762` shows BlobRef preview paths use direct Blob multipart upload, `blob://` references, Tauri cache-first fetch, and browser object URLs; focused BlobRef/converter tests passed.
- No frontend UI files were modified in this discovery parent; only ledger and scan artifacts were added.

## Known Gaps

- Remediation candidate: remove or strictly narrow legacy `events` rendering in `novaic-app/src/components/Chat/AssistantMessage.tsx`.
- No remediation candidate was found in active Monitor shell artifact projection.
- No remediation candidate was found in active BlobRef/artifact preview handling.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p779-chat-shell-output-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p780-monitor-shell-artifact-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p781-blob-artifact-preview-scan.txt`
- Child result IDs: `R760`, `R761`, `R762`
