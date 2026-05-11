# P000: Audit and fix shell CLIs to obey blob artifact contract

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Shell-exposed CLIs such as `devicectl`, `agentctl`, and `cortex` can return large or binary-like payloads through stdout. The concrete failure surfaced through `devicectl hd screenshot`, which printed a large base64 JPEG into stdout instead of returning a `tool-output.v1` artifact with a `blob://...` URI. This violates the blob/tool-output contract and forces downstream shell preview truncation, Cortex payload externalization, and context assembly to carry data that should have been an artifact.

We need comprehensively audit all shell CLIs and fix live CLI paths so binary, media, file, and large structured outputs use blob-backed artifact manifests, while stdout stays bounded and semantically useful.

## Success Criteria
- All shell-exposed CLI commands are inventoried by command surface and output type.
- Any CLI that can emit screenshots, files, media, or large binary/base64 content returns `tool-output.v1` with `artifacts[].uri` using `blob://...` instead of embedding the content in stdout text.
- CLI text output remains small and useful; raw base64 screenshots are not printed as the primary shell stdout contract.
- Tests prove the screenshot path and any other touched artifact-producing paths obey the blob contract.
- Residual old/direct/base64 CLI output paths are either removed or explicitly justified as non-live/test-only.

## Subproblems
- P001: Inventory shell CLI surfaces and blob-contract risks
- P002: Fix devicectl artifact-producing commands to use blob contract
- P003: Audit and fix agentctl and cortex CLI outputs
- P004: Verify CLI blob contract and clean residual old behavior

## Results
- R008

## Latest Check
C008

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R008: problems/P000/results/R008.md
- Check C008: problems/P000/checks/C008.md

## Follow-ups
- none
