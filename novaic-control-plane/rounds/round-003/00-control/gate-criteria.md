# Round 003 Gate Criteria

## Gate A - Migration Evidence
- Every DONE item includes: `repo_url`, `branch`, `commit_sha`, `migrated_paths`, `artifact_path`.
- Monorepo source path and target repo path mapping is explicit.

## Gate B - Operability
- At least 2 split repos pass startup/health checks from their own repository roots.
- Operability evidence includes command and expected marker output.

## Gate C - Integration
- At least 1 cross-repo call path is replayed and marked PASS.
- Contract version used in replay is recorded.

## Gate D - Governance
- Incomplete items contain blocker owner and `target_round`.
- No team marks DONE for plan-only or doc-only output.

## Fail Conditions
- DONE without migrated code commit
- missing repo URL or commit SHA
- script-only evidence without corresponding code move
