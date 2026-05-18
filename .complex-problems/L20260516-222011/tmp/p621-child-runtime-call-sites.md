# Runtime Sandbox SDK Call Site Residue

## Problem

Audit active runtime shell/tool execution call sites to verify they use the sandbox SDK/service boundary and do not perform direct subprocess execution, host path mounting, or legacy local fallback.

## Success Criteria

- Records exact scans over `novaic-agent-runtime` call sites for sandbox SDK imports, shell execution, subprocess/process/local/fallback/host/mount terms.
- Cites the runtime source slices that instantiate or call the sandbox SDK.
- Confirms active runtime shell/tool handlers call the SDK/service boundary.
- Creates a remediation follow-up if any active runtime path bypasses sandboxd.
