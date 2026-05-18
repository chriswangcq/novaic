# Review and patch Device/artifact/display remediation candidates

## Summary

Review the exact remediation candidates from discovery and patch only safe active stale docs/code claims. Split any risky or broad route/API migration into a child problem instead of hiding it in a one-go ticket.

## Problem Definition

Discovery found no active shell/history base64 leak, but it did find stale or legacy surfaces that can mislead future implementation: one stale VMuse doc, one VMuse cleanup residue, and one mounted Device screenshot route that still returns inline MCP image content.

## Proposed Solution

Patch safe stale docs/code immediately. For the Device screenshot route, inspect callers and ownership before changing behavior; if route retirement/conversion is not clearly safe, split it into a dedicated child problem.

## Acceptance Criteria

- Every discovery cleanup candidate is dispositioned.
- Safe code/doc cleanups are implemented.
- Generated resource copies are not manually patched unless sync is required and verified.
- Risky Device route migration is either completed with tests or split into an explicit child problem.
- Focused tests/checks are run for touched packages.

## Verification Plan

- Search for route/caller references before changing Device behavior.
- Run focused tests for touched packages.
- Run resource-hygiene check if VMuse source package changes.
- Re-scan media/base64/doc hits after edits to ensure no new stale residue remains.

## Scope

Candidates to disposition:

1. `docs/mcp-vmuse/mcp-protocol-mapping.md`
   - Update or mark historical so it no longer claims Runtime directly exposes VMuse MCP tools to the LLM as the live design.
2. `novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/windows.py`
   - Remove unused `base64` import if still unused.
   - If source package changes, sync generated/copy resource directories only through the established resource-hygiene path.
3. `novaic-device/device/vmcontrol_routes.py`
   - Review mounted screenshot route returning inline MCP image content.
   - If safe and obviously legacy/debug-only, retire or convert.
   - If not safe, spawn a blocking child problem with route ownership, callers, compatibility, and migration tests.

## Extra Scope Notes

Do not manually patch generated VMuse copies unless the source package change requires a sync step and the resource-hygiene script confirms the copies are correct.
