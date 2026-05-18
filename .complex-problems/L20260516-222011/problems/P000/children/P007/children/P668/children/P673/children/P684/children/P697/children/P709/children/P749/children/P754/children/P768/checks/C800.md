# App Tauri backend and VmControl wiring discovery check

## Summary

Success. P768's split discovery is complete and sufficiently evidenced. It did not fix the stale script/package graph, but the problem was discovery-only and the exact remediation candidates are now identified.

## Evidence

- `R754` aggregates child results `R751`, `R752`, and `R753`.
- `R751` proves Rust VMUSE service wiring targets `novaic_mcp_vmuse.http_server`.
- `R752` proves local backend startup still omits Cortex/Sandboxd while passing `--cortex-url`, and identifies the `19996` port conflict.
- `R753` proves source/generation synchronization for key resource scripts/config and identifies generated/backend bundle drift.
- All child checks `C797`, `C798`, and `C799` succeeded.

## Criteria Map

- Relevant Tauri Rust/setup/backend startup/resource wiring files discovered: satisfied across P770/P771/P772.
- Suspicious hits around VMUSE/FastMCP/devicectl/display/screenshot/Blob/Sandbox/LogicalFS classified: satisfied by child results separating Rust HTTP route wiring, script/service graph issues, and resource packaging drift.
- Exact remediation candidates listed or absence recorded: satisfied by the parent candidate list in `R754`.
- No Tauri/app wiring files modified: satisfied because all P768 children were discovery-only and wrote only ledger artifacts.

## Execution Map

- The parent split ticket created three child problems and waited for them to close.
- Each child completed bounded read-only scans with scan artifacts and strict checks.
- The parent result summarized child findings without adding unverified claims.

## Stress Test

- Plausible failure mode: the old VMUSE FastMCP route could still be launched by Rust setup. `R751` inspected service unit code and found HTTP server startup.
- Plausible failure mode: current app failures could come from scripts rather than Rust. `R752` found concrete script/service graph inconsistencies.
- Plausible failure mode: generated resources could drift silently. `R753` compared checksums and found both synchronized stale text resources and a generated-only backend binary.

## Residual Risk

- Remediation is still pending and should be handled by later tickets. This check only closes discovery.
- Runtime behavior was not smoke-tested under app launch because P768 was a static discovery branch.

## Result IDs

- R754
