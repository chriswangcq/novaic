# VMuse Runtime URL Config Contract Remediation

## Problem

`services.json` still contains `runtime.vmuse_mcp_url` pointing at `http://127.0.0.1:8080/mcp`, while VMuse was cleaned to an HTTP JSON server. The field may be unused, stale, or still consumed by app/runtime code, so usage must be inspected before changing it.

## Success Criteria

- Active consumers of `vmuse_mcp_url` are identified.
- If the field is active, its name/value/usage are updated to the current HTTP JSON contract.
- If the field is inactive, it is removed or quarantined with a narrow cleanup note so stale `/mcp` config no longer looks authoritative.
- Resource and generated `services.json` copies remain synchronized after any change.
- Targeted scans for `vmuse_mcp_url`, `/mcp`, and VMuse HTTP endpoints show only intentional references.
