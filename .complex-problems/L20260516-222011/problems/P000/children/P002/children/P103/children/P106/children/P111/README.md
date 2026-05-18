# Devicectl Artifact-Producing Commands Contract Audit

## Problem

`devicectl hd screenshot` and `devicectl hd file-pull` produce media/file payloads and must upload to Blob Service and print `tool-output.v1` artifact manifests, not inline base64/data fields.

## Success Criteria

- Inspect artifact-producing devicectl implementation.
- Verify screenshot and file-pull upload to blob and omit base64/raw data from stdout.
- Run focused fake-server tests for artifact contract.
- Fix bounded gaps found.
