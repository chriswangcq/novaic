# Active docs and scripts semantic residue discovery result

## Summary

Completed a read-only scan of active docs and scripts for service-boundary residue. No product files were modified by this discovery ticket.

The active docs/scripts are mostly aligned with the current architecture: Gateway is thin edge, Business is product/domain hub, Device owns hardware/CloudBridge, Queue/Runtime own execution coordination, Cortex owns scope/context semantics, Blob owns bytes, Sandboxd executes processes, and shell/display media output is bounded text plus Blob manifests and explicit display projection.

## Scans Performed

- Listed active docs/scripts with `find docs scripts -maxdepth 2 -type f`.
- Scanned docs/scripts for service-boundary terms: Cortex, Gateway, Business, Queue Service, Runtime, Device, devicectl, Blob, LogicalFS, Sandboxd, display, VMuse, VmControl.
- Scanned docs/scripts for risky residue terms: base64, inline image, MCP image, screenshot, artifact, blob refs, tool-output, direct Blob, fallback, compat, legacy, deprecated, old path, TODO, FIXME.
- Spot-read the most relevant active docs:
  - `docs/gateway/internal-and-workers.md`
  - `docs/blob-service-architecture.md`
  - `docs/architecture/logicalfs-realtime-file-authority.md`
  - `docs/runtime/tool-chain-dispatch.md`
  - `docs/architecture/cortex.md`
  - `docs/cortex-architecture.md`
  - `docs/architecture/data-ownership.md`
  - `docs/reference/blob-service.md`
- Checked current `novaic-logicalfs/README.md` and `novaic-sandbox-service/main_sandbox_service.py` to compare docs against actual module shape.

## Classification

Current and acceptable:
- `docs/gateway/*.md` now consistently describes Gateway as edge/auth/App WS/signaling/Blob edge, with Business and Device owning product and hardware paths.
- `scripts/start.sh` reflects the current service topology and launches Sandboxd plus Cortex with explicit service URLs.
- `docs/runtime/tool-chain-dispatch.md` correctly states shell as bounded terminal text, media CLIs as `tool-output.v1` Blob manifests, and `display(blob://...)` as explicit current-round perception.
- `docs/reference/blob-service.md` and `docs/blob-service-architecture.md` correctly keep Blob as byte/object infrastructure, not product meaning or live RO/RW semantics.
- Roadmap/ticket docs contain many legacy/fallback/direct-path references, but they are mostly historical work records rather than active instructions.

Remediation candidates for the next child:
- `docs/architecture/logicalfs-realtime-file-authority.md` says “LogicalFS is the semantic authority” and has a “LogicalFS Service” section, while `novaic-logicalfs/README.md` says LogicalFS is business-agnostic, does not know Cortex/agents/subagents/process execution, and workspace state ownership belongs to the caller. The doc should be sharpened to “file-operation/view authority/substrate” and keep Cortex as semantic owner.
- `docs/architecture/cortex.md` and `docs/cortex-architecture.md` list `sandbox.py` as “物化 workspace → shell → 回写 /rw”. After Sandboxd and LogicalFS extraction this phrasing is too ownership-heavy; it should say Cortex orchestrates shell/workspace semantics, delegates process execution to Sandboxd, and uses LogicalFS substrate/view/patch semantics.
- `docs/architecture/data-ownership.md` says “Cortex + LogicalFS file authority”. This is directionally correct, but can be made crisper: Cortex owns scope/context/workspace semantics; LogicalFS owns live RO/RW file operations/view contract; Blob owns bytes.

No immediate docs/scripts remediation candidate was found in `docs/gateway/internal-and-workers.md`, `docs/runtime/tool-chain-dispatch.md`, `docs/reference/blob-service.md`, or `scripts/start.sh`.

## Verification

`git diff --name-only -- docs scripts` shows pre-existing docs/script changes from earlier ledger branches, but this P752 discovery step did not patch product docs/scripts. The only files added for this step are ledger tmp files under `.complex-problems/L20260516-222011/tmp/`.

## Residual Risk

This discovery child did not inspect service code or generated app resources; those are covered by sibling discovery problems `P753` and `P754`.
