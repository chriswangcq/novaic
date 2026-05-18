# Result: P712 Patch active Cortex boundary residue

## Summary
Patched the bounded active Cortex boundary residue from P711/P710. The touched wording now describes Cortex as semantic scope/context/work-trace/payload-manifest and shell/sandbox orchestration, while explicitly leaving LogicalFS/Blob as file authority and Sandboxd as process execution authority.

## Files Changed
- `scripts/start.sh`
- `docs/architecture/service-topology.md`
- `docs/cortex-architecture.md`

## Changes
- `scripts/start.sh`: replaced `Workspace, Sandbox` ownership wording with `Scope/context/work trace, payload manifest, shell orchestration`.
- `docs/architecture/service-topology.md`: replaced Cortex `payload manifest/sandbox` wording with `payload manifest、shell/sandbox orchestration`.
- `docs/cortex-architecture.md`: replaced `Workspace、Sandbox` wording with `Workspace 语义、shell/sandbox 编排`, and explicitly says LogicalFS/Blob own lower file authority while Sandboxd owns process execution.

## Verification
- Retired phrase scan over touched active files found 0 matches.
- Focused boundary scan recorded remaining intentional/current mentions.
- `python3 scripts/ci/lint_blob_workspace_boundary.py` passed with `Blob workspace boundary OK`.

## Evidence
- `.complex-problems/L20260516-222011/tmp/p712/remediation.diff`
- `.complex-problems/L20260516-222011/tmp/p712/retired-phrase-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p712/focused-boundary-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p712/lint-blob-workspace-boundary.txt`

## Residual Risk
`docs/architecture/service-topology.md` still contains an intentional comparison row `Cortex/Sandbox/Runtime 各自提供实时 RO/RW 文件服务 -> LogicalFS...`; it is a historical/old-vs-new contrast table, not active ownership wording. No patch was needed there.
