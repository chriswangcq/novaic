# App chat audio and blob upload residue classification

## Problem

Chat/audio/blob upload code contains base64/data URL and fallback guard hits, including tiny silent audio placeholders and tests that ban base64 upload paths. These need classification against the current blob-first contract.

## Success Criteria

- Inspect chat audio, voice recording, blob attachment, and upload path hits for base64/data URL/fallback residue.
- Classify each as current browser/audio primitive, guard against old base64 upload, stale residue, or active risk.
- Clean stale comments/wording where safe without changing browser audio behavior unnecessarily.
- Run focused tests for blob/audio upload guards or document no-code-change verification.
