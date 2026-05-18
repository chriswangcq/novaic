# Remove Stale VMuse MCP URL Config

## Problem Definition

App service config still exposes `runtime.vmuse_mcp_url = http://127.0.0.1:8080/mcp`, but VMuse is now an HTTP JSON service and no active consumer of that exact config key has been found. Keeping the field makes stale MCP transport look authoritative.

## Proposed Solution

Confirm active consumers of `vmuse_mcp_url`; if none exist, remove the stale config field from both resource and generated `services.json` copies. Keep only intentional `/mcp` references outside this field, such as gateway MCP routes or virtio port naming.

## Acceptance Criteria

- Active consumer search for `vmuse_mcp_url` is recorded.
- `vmuse_mcp_url` is removed if inactive.
- Resource and generated `services.json` copies remain synchronized and valid JSON.
- Targeted scans for `vmuse_mcp_url`, `8080/mcp`, and relevant `/mcp` references show no stale VMuse runtime config.

## Verification Plan

- Run `rg` over app/runtime/gateway/cortex/scripts for `vmuse_mcp_url` and `8080/mcp`.
- Parse both service config copies with `python -m json.tool`.
- Compare both service config copies with `cmp`.
- Run a targeted scan for `/mcp` and classify remaining matches.

## Risks

- Some external manual process might still read `services.json`, but no in-repo active consumer should justify preserving stale config.

## Assumptions

- VMuse HTTP JSON routes are the current transport contract.
- Config fields with no active consumer should be removed rather than kept for compatibility.
