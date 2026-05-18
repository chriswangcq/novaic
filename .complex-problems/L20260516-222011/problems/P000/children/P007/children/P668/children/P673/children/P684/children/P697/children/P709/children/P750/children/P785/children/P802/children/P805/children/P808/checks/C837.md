# VMuse Runtime URL Config Contract Check

## Summary

Success. R789 removes the stale `vmuse_mcp_url` field after verifying it has no active in-repo consumer, keeps config copies synchronized, and confirms remaining `/mcp` references are unrelated to the VMuse runtime config.

## Evidence

- R789 records an active consumer scan for `vmuse_mcp_url|8080/mcp` with no remaining matches.
- R789 removes the key from both resource and generated service config copies.
- R789 verifies both JSON files parse and are byte-identical.
- R789 classifies remaining `/mcp` matches as gateway dynamic MCP routes and virtio port naming.

## Criteria Map

- Active consumers identified: satisfied by the recorded scan.
- Inactive field removed/quarantined: satisfied by removing `runtime.vmuse_mcp_url`.
- Resource and generated configs synchronized: satisfied by `cmp`.
- Targeted scans show only intentional references: satisfied.

## Execution Map

- Config field removed in both copies.
- JSON and scan verification performed immediately.

## Stress Test

- Checked not just `vmuse_mcp_url` but also raw `8080/mcp`, preventing a renamed stale field from slipping through.

## Residual Risk

- VMuse resource sync script has a stale `main.py` check; it is not part of the runtime URL config and remains visible as a separate app resource hygiene concern.

## Result IDs

- R789
