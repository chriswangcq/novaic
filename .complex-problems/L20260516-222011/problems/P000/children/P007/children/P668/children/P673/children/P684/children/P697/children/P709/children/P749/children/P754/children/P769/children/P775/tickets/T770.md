# App shell artifact output UI contract discovery ticket

## Problem Definition

The shell output contract is now supposed to behave like a terminal: user-visible tool output is bounded text, while large/rich outputs are represented by artifact/blob manifests. App UI code may still assume shell stdout can contain rich JSON/media payloads, parse media payloads directly, preview embedded data, or expose artifact manifests incorrectly.

## Proposed Solution

Run bounded source discovery in `novaic-app/src` for shell/tool output rendering, activity timeline, tool-call monitor rows, artifact/blob manifest handling, display/image preview integration, truncation, and any UI copy/detail affordances that reference shell stdout or `tool-output.v1`. Inspect high-signal files and classify each suspicious path as contract-compliant, legitimate BlobRef/image rendering, dead residue, or remediation candidate.

## Acceptance Criteria

- Relevant shell/tool output, artifact manifest, monitor timeline, and tool-call UI files are discovered.
- Hits for `tool-output.v1`, artifacts, Blob refs, shell stdout, truncation, display, and media preview are classified.
- Exact remediation candidates are listed if the App UI still expects shell-rich payloads or unsafe direct media content.
- No frontend UI files are modified in this discovery ticket.

## Verification Plan

Use `rg --files`, targeted `rg -n -i`, and focused source slices under `novaic-app/src`. Check existing guard tests for activity timeline, chat attachments, BlobRef paths, and shell/artifact output. If the discovery reveals active remediation candidates, list exact files and line-level behaviors for follow-up implementation tickets.

## Assumptions

- App UI source lives under `novaic-app/src`.
- Shell runtime projection itself is outside this discovery ticket unless App imports or tests explicitly encode assumptions about it.
- BlobRef/image preview rendering is acceptable when it works through `blob://` references rather than raw base64/data URL payloads.

## Risks

- Some artifact manifest strings may be intentionally displayed as terminal text; classify terminal text separately from parsed/rich UI affordances.
- Monitor timeline and chat display may use different projections; do not assume one covers the other without reading both.
