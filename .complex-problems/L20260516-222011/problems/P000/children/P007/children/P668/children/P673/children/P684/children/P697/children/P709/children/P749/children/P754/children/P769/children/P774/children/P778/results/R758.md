# App raw JSON and truncation primitives discovery result

## Summary

Shared raw JSON/truncation primitive discovery found one high-risk but currently unused primitive: `novaic-app/src/components/Visual/SmartValue.tsx`. It recursively renders arbitrary strings/objects and copies raw values with `JSON.stringify`, with only length collapsing and no `_mcp_content`/base64/data URL/binary scrub. It currently appears unused outside its own module, so it is not an active leak path but is dangerous residue under the project's "residual code hurts" principle. Other suspicious hits are legitimate chat media rendering, ActivityTimeline scrubbing, WebRTC cursor rendering, tests, or explicit settings fields.

## Done

- Scanned shared frontend primitives for JSON/value/truncation/copy/media rendering.
- Inspected `SmartValue.tsx`, usage references, and settings cleanup result rendering.
- Classified base64/data URL/BlobRef/artifact hits across app primitives.

## Verification

- Scan artifact: `.complex-problems/L20260516-222011/tmp/p778-json-primitives-scan.txt`.
- `rg -n "<SmartValue|SmartValue\\(|JsonTree|CollapsibleText|ImagePreview" novaic-app/src -g '*.tsx' -g '*.ts'` only found `SmartValue`/`JsonTree`/`CollapsibleText` references inside `SmartValue.tsx`, so `SmartValue` appears unused.
- `SmartValue.tsx` renders arbitrary objects via `JsonTree`, long text via `CollapsibleText`, and raw copy through `JSON.stringify(value, null, 2)`.
- `SmartValue.tsx` renders `blob://` or http image strings through `ImagePreview`/`useAuthenticatedImage`, which is legitimate BlobRef rendering but has no binary-string scrub for non-image strings.
- `SettingsModal.tsx` renders cleanup result through explicit fields, not `SmartValue`.
- `ActivityTimeline.tsx` raw payload detection is a safe scrubbing primitive, not a leak.
- `VoiceMessageBubble.tsx` and `useWebRtc.ts` base64/data URL hits are UI/device rendering mechanics, not shared raw JSON/detail primitives.

## Known Gaps

- Remediation candidate: remove unused `novaic-app/src/components/Visual/SmartValue.tsx` if no active import exists. If it must stay, add explicit safe projection and tests before any reuse.
- No shared UI primitive files were modified in this discovery child.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p778-json-primitives-scan.txt`
