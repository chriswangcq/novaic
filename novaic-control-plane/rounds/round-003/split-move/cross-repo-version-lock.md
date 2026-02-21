# Round 003 Cross-Repo Version Lock

## Contract/dependency lock (for migration replay)

- contract_set: `contracts@v2.1.0-rc1`
- compatibility_baseline: `compatibility-v2`
- python_min: `3.10`
- fastapi: `0.115.x`
- uvicorn: `0.30.x`

## Repo lock table

| repo | repo_url | branch | commit_sha | lock_notes |
|---|---|---|---|---|
| `novaic-gateway` | `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-gateway` | `main` | `a9ba15cda1312943dfee7675acf92a24013612a1` | migrated MCP gateway health entrypoint |
| `novaic-runtime-orchestrator` | `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-runtime-orchestrator` | `main` | `fc7611e0948241bc4b73369ea32239562ff16254` | migrated runtime health entrypoint |
| `novaic-tools-server` | `file:///Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-003/split-move/repos/novaic-tools-server` | `main` | `33ffcc181363ed168796d773d1a5f961d8ba8f07` | migrated tools health entrypoint |

## Migrated path mapping (source -> target)

- `novaic-gateway/mcp_main.py` -> `repos/novaic-gateway/services/mcp_gateway.py`
- `novaic-backend/main_runtime_orchestrator.py` -> `repos/novaic-runtime-orchestrator/runtime_orchestrator/main.py`
- `novaic-backend/main_tools.py` -> `repos/novaic-tools-server/tools_server/main.py`
