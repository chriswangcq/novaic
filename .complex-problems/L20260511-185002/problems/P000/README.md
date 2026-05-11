# Audit and fix shell CLIs to obey blob artifact contract

## Problem

Shell-exposed CLIs such as `devicectl`, `agentctl`, and `cortex` can return large or binary-like payloads through stdout. The concrete failure surfaced through `devicectl hd screenshot`, which printed a large base64 JPEG into stdout instead of returning a `tool-output.v1` artifact with a `blob://...` URI. This violates the blob/tool-output contract and forces downstream shell preview truncation, Cortex payload externalization, and context assembly to carry data that should have been an artifact.

We need comprehensively audit all shell CLIs and fix live CLI paths so binary, media, file, and large structured outputs use blob-backed artifact manifests, while stdout stays bounded and semantically useful.

## Success Criteria

- All shell-exposed CLI commands are inventoried by command surface and output type.
- Any CLI that can emit screenshots, files, media, or large binary/base64 content returns `tool-output.v1` with `artifacts[].uri` using `blob://...` instead of embedding the content in stdout text.
- CLI text output remains small and useful; raw base64 screenshots are not printed as the primary shell stdout contract.
- Tests prove the screenshot path and any other touched artifact-producing paths obey the blob contract.
- Residual old/direct/base64 CLI output paths are either removed or explicitly justified as non-live/test-only.
