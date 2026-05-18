# Result: P711 Cortex boundary residue remediation and verification

## Summary
The execution found active Cortex boundary residue candidates but did not complete remediation in this execution attempt. This should not be considered successful until a follow-up patch pass handles the active candidates.

## Evidence
Pre-scan artifact: `.complex-problems/L20260516-222011/tmp/p711/pre-scan.txt`

Active candidates found:
- `scripts/start.sh:18` — Cortex comment says `Scope tree, LLM context assembly, Workspace, Sandbox`.
- `docs/architecture/service-topology.md:29` — Cortex row says `Agent scope/context/work trace/payload manifest/sandbox`.
- `docs/cortex-architecture.md:31` — text says Cortex still provides Workspace, Sandbox, and capability JWT.

Non-blocking/contextual candidate:
- `docs/architecture/service-topology.md:131` describes the old incorrect idea and immediately maps it to `LogicalFS is Cortex/shell realtime RO/RW authority`; this may be intentional contrast, but should be checked in the follow-up.

## Status
Not complete. A follow-up remediation ticket is required to patch safe active wording, then run focused scans and any relevant boundary lint.
