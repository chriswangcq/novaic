# Audit Shell Wrapper Terminal Output Boundary

## Problem Definition

P614 must verify shell wrapper/tool-facing output returns bounded terminal text and artifact manifests instead of raw media/base64 bytes in LLM history.

## Proposed Solution

Scan shell wrapper/capability modules and tests for truncation, tool-output.v1, artifacts, devicectl wrapping, and base64/media handling. Cite exact code slices and run focused shell output/blob contract tests.

## Acceptance Criteria

- Shell wrapper scan and slices are recorded.
- Code evidence shows artifact-producing device/file commands print BlobRef manifests instead of base64.
- Focused shell output/blob contract tests pass.
- Any raw media/base64 history path is captured as follow-up.

## Verification Plan

Run `test_shell_capabilities_blob_contract.py`, `test_tool_output_contract.py`, and `test_shell_output_contract.py` if available.

## Risks

- There may be several shell wrapper layers; scan must include Cortex shell capabilities and runtime tool contract tests.

## Assumptions

- Shell is allowed to print terminal text; it should not inline large media payloads when wrappers can produce artifacts.
