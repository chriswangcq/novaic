# Round 003 Repo Bootstrap Status

## First-wave repos

| repo | repo_url | owner | default_branch | bootstrap_commit_sha |
|---|---|---|---|---|
| `novaic-gateway` | `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway` | `API Team` | `main` | `a9ba15cda1312943dfee7675acf92a24013612a1` |
| `novaic-runtime-orchestrator` | `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-runtime-orchestrator` | `Runtime Team` | `main` | `fc7611e0948241bc4b73369ea32239562ff16254` |
| `novaic-tools-server` | `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-tools-server` | `Tools Team` | `main` | `33ffcc181363ed168796d773d1a5f961d8ba8f07` |

## Migrated path mapping (source -> target)

- `novaic-gateway/mcp_main.py` -> `repos/novaic-gateway/services/mcp_gateway.py`
- `novaic-backend/main_runtime_orchestrator.py` -> `repos/novaic-runtime-orchestrator/runtime_orchestrator/main.py`
- `novaic-backend/main_tools.py` -> `repos/novaic-tools-server/tools_server/main.py`

## Bootstrap baseline

- `CODEOWNERS` exists in each repo under `.github/CODEOWNERS`.
- base CI exists in each repo under `.github/workflows/ci.yml`.
- branch protection baseline documented in each repo as `BRANCH_PROTECTION_BASELINE.md`.
