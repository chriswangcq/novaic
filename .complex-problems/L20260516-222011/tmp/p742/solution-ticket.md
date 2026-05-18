# Patch VMuse protocol mapping doc

## Summary

Update `docs/mcp-vmuse/mcp-protocol-mapping.md` so it reflects the current shell/device-proxy plus Blob/display boundary instead of implying live direct VMuse MCP media exposure to the LLM.

## Problem Definition

The documentation is stale relative to the current architecture and can mislead future maintainers into reintroducing direct MCP image/media tool exposure.

## Proposed Solution

Edit only the stale documentation claims. Mark historical direct MCP mapping as legacy if useful, and describe the current contract: shell returns terminal text plus `tool-output.v1` Blob manifests; history is manifest-only; `display` is the explicit current-round visual perception path.

## Acceptance Criteria

- `docs/mcp-vmuse/mcp-protocol-mapping.md` no longer presents direct Runtime-to-LLM VMuse MCP media exposure as the live path.
- The current shell/Blob/display contract is stated clearly.
- No code behavior changes are included in this ticket.

## Verification Plan

- Inspect the edited doc.
- Run targeted grep for stale direct-exposure wording in that doc.
