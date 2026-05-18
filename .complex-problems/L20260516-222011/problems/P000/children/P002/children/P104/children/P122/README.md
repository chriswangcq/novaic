# Artifact-Producing CLI Blob Manifest Contract Audit

## Problem

Media-producing shell CLIs such as `devicectl hd screenshot` and file-pull paths must return bounded text plus `tool-output.v1` artifact manifests with `blob://runtime-artifact/...` refs, not raw bytes or base64 in stdout.

## Success Criteria

- Inspect artifact manifest helper and relevant shell capability CLI implementations.
- Verify screenshot/file-pull outputs contain `tool-output.v1` and blob artifact metadata.
- Verify raw base64 payloads are absent from stdout.
- Fix missing guards for any media CLI path found leaking raw bytes.
