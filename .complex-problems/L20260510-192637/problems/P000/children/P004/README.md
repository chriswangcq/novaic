# Blob Payload Authority Contract

## Problem

Large tool payload bytes are stored in Blob Service while Workspace holds semantic refs. This is probably correct, but the authority contract must be explicit so Blob does not become a hidden semantic store.

## Success Criteria

- Define Blob as raw byte/artifact authority only.
- Define where semantic metadata and lifecycle refs live.
- Specify verification for payload fetch, missing blob behavior, retention, and cleanup.
