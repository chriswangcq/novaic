# App Backend Startup Graph Remediation

## Problem Definition

The app backend startup graph currently has drift between source/dev startup, packaged startup, generated assets, and app service config. The audit found three concrete issues: packaged scripts look for `novaic-blob-service` while generated assets contain `novaic-storage-a`, source resources do not carry that blob binary, and the source/dev script names port `19996` as Cortex while app config names it `vmcontrol`. VMuse config also still references `/mcp` and needs usage inspection before deciding whether to patch.

## Proposed Solution

Remediate the graph in small, evidence-backed steps:

1. Inspect active consumers of `services.json`, `vmuse_mcp_url`, `--cortex-url`, and packaged backend scripts.
2. Patch only source-of-truth files first, then mechanically synchronize resource/generated copies where they are committed duplicates.
3. Make blob service binary expectations match committed binaries, either by aligning script detection to the committed binary name or by synchronizing the missing binary resource if that is the intended packaged source.
4. Clarify the dev script port model so `19996` is not ambiguously called Cortex when app config says `vmcontrol`.
5. Remove or update stale VMuse `/mcp` config only if active usage confirms it is part of the startup graph.

## Acceptance Criteria

- Source/dev and packaged startup scripts no longer disagree with committed backend binary names.
- Resource and generated packaged script/config copies are either byte-identical where they should be duplicated or explicitly documented as dev/generated boundaries.
- `19996` is no longer ambiguously represented as both Cortex and vmcontrol in the same startup graph.
- VMuse service URL config is either updated to the HTTP JSON contract or proven inactive and quarantined for cleanup.
- No generated/source divergence is introduced.

## Verification Plan

- Run targeted `rg` scans for `PORT_CORTEX`, `vmcontrol`, `vmuse_mcp_url`, `novaic-blob-service`, `novaic-storage-a`, `BLOB_SERVICE`, and `--cortex-url`.
- Run `bash -n` on all committed startup scripts.
- Compare resource and generated packaged script/config copies with `diff` or `cmp` after synchronization.
- Run any narrow unit/contract tests available for app service config or VMuse resource contract.

## Risks

- The generated asset tree may contain build outputs that should not be hand-edited; remediation must distinguish source resources from generated committed copies.
- Worker `--cortex-url` arguments may still be required by runtime code even when Cortex is not started by the dev app script.
- Blob binary naming may be historical (`novaic-storage-a`) rather than a simple typo.

## Assumptions

- P804 audit evidence is accurate and should be used as the concrete starting point.
- The goal is not backward compatibility with stale names; the final graph should be internally consistent and easier to reason about.
