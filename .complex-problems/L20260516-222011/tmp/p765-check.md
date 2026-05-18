# VMuse service residue discovery check

## Summary

Success. Result R746 solves P765 because it discovered and scanned VMuse, classified the current HTTP/base64 lower-level protocol separately from stale direct FastMCP media exposure, ran the focused VMuse test, and listed exact remediation candidates without modifying product code.

## Evidence

- R746 records the scan artifact `.complex-problems/L20260516-222011/tmp/p765-vmuse-scan.txt`.
- R746 cites inspected files across FastMCP entrypoints, HTTP server, desktop tools, contract marker tests, and package metadata.
- R746 records `PYTHONPATH=novaic-mcp-vmuse/src pytest -q novaic-mcp-vmuse/tests` with `1 passed in 0.01s`.
- R746 lists the exact stale FastMCP direct media entry path to remediate.

## Criteria Map

- Criterion: VMuse source files are discovered and scanned with bounded commands.
  Evidence: R746 Done items 1-2 and scan artifact.
- Criterion: Suspicious hits are classified as current lower-level media protocol, shell artifact boundary, stale residue, or unrelated vocabulary.
  Evidence: R746 Verification distinguishes `http_server.py` and `tools/desktop.py` lower-level base64 transport from stale `main.py` FastMCP direct `ImageContent` exposure.
- Criterion: Exact remediation candidates are listed, or absence is explicitly recorded.
  Evidence: R746 Known Gaps lists `main.py`, `cli.py`, `__init__.py`, and `pyproject.toml` remediation targets.
- Criterion: No product code is modified in this discovery child.
  Evidence: R746 Known Gaps states no product code was modified.

## Execution Map

- Ticket T756 was classified one_go because this was a bounded VMuse source discovery task.
- Execution scanned files, inspected representative code, checked references, and ran the available VMuse test.
- Result R746 recorded the current/stale boundary distinction and exact cleanup candidates.

## Stress Test

- Plausible failure mode: all base64 in VMuse could be treated as bad, even though VMuse lower-level HTTP transport currently returns screenshot bytes to the outer device/runtime wrapper.
- Check result: R746 avoids this false positive and only flags direct MCP `ImageContent` exposure as stale.
- Plausible failure mode: old FastMCP code might be dismissed as harmless dead code.
- Check result: R746 notes it remains reachable through `cli.py` and `pyproject.toml`, so it is a real cleanup candidate.

## Residual Risk

- Medium but non-blocking for P765. Discovery is complete, but the remediation branch must physically remove or disable the stale FastMCP entry path and mirrored app copies.

## Result IDs

- R746
