# Phase 4 Blob Payload Manifest

## Problem

Blob raw bytes need semantic manifests so Blob does not become hidden semantic authority.

## Success Criteria

- Record payload manifests in SQLite/Workspace when payloads are externalized.
- Fetch/missing/corrupt payload behavior is explicit.
- Tests cover externalization, missing blob, manifest lookup, retention markers.
