# Non-Author Replay Artifact - API Gateway (Round 007)

## Metadata
- replay_timestamp: 20260221T022324Z
- operator_id: ci-api-round007
- round: round-007
- repo_url: file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway
- commit_sha: e9cad76b7a79e289344bf8745cdb04d7a50702e5
- branch: round-003-split
- canonical_url_policy: file:///absolute/path/to/<repo-root>

## Canonical URL Verification
- old_url: file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/remotes/novaic-gateway.git
- new_canonical_url: file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway
- reason: bare remote path (.git suffix) replaced with working-tree repo root per canonical-repo-url-policy

## Replay Command
```
bash novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh
```
Run from: workspace root (`/Users/wangchaoqun/novaic`)

## Observed Output (Round 007 execution)
```
FIXED_CHAIN_RUNTIME_HEALTH=PASS
FIXED_CHAIN_GATEWAY_HEALTH=PASS
FIXED_CHAIN_FORWARD_HEALTH=PASS
SPLIT_FIXED_RUNTIME_CHAIN=PASS
SPLIT_RUNTIME_HEALTH=PASS
SPLIT_GATEWAY_HEALTH=PASS
SPLIT_TOOLS_HEALTH=PASS
SPLIT_GATEWAY_STATUS_ROUTE=PASS
SPLIT_E2E_RUNTIME_FORWARD=PASS
```

## Required Markers
- FIXED_CHAIN_RUNTIME_HEALTH=PASS
- FIXED_CHAIN_GATEWAY_HEALTH=PASS
- FIXED_CHAIN_FORWARD_HEALTH=PASS
- SPLIT_FIXED_RUNTIME_CHAIN=PASS
- SPLIT_RUNTIME_HEALTH=PASS
- SPLIT_GATEWAY_HEALTH=PASS
- SPLIT_GATEWAY_STATUS_ROUTE=PASS
- SPLIT_E2E_RUNTIME_FORWARD=PASS
- CANONICAL_URL_UPDATED=PASS

## Canonical URL Update Verification
- CANONICAL_URL_UPDATED=PASS
- old_format: file:///...remotes/novaic-gateway.git (bare remote, rejected by policy)
- new_format: file:///...repos/novaic-gateway (working-tree root, compliant)

## Conclusion
All 9 runtime/gateway split chain markers green. Canonical repo_url updated from bare-remote path to working-tree repo root per Round 007 policy. No regressions introduced.
