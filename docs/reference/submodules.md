# 仓库与子模块

> 对应 **`HANDOVER.md` §三**。权威清单：根目录 **`.gitmodules`**。

```bash
git clone --recurse-submodules git@github.com:chriswangcq/novaic.git
git submodule update --init --recursive
```

## Submodule 一览

| 目录 | 用途 |
|------|------|
| `novaic-app` | Tauri 桌面 + 移动端 |
| `novaic-gateway` | 云端 Gateway |
| `novaic-llm-factory` | LLM Factory |
| `novaic-quic-service` | STUN + Relay |
| `novaic-agent-runtime` | Agent 运行时（Task/Saga/Workers） |
| `novaic-mcp-vmuse` | MCP VMuse |
| `novaic-contracts` | 协议与类型 |
| `novaic-common` | 共享库与配置（含 `config/services.json`） |
| `novaic-storage-a` | File Service |
| `novaic-cortex` | Cortex HTTP |
| `novaic-control-plane` | 控制面板 |
| `Entangled` | 同步引擎（Python/Rust 等） |
| `thirdparty/openclaw` | 上游参考（非线上服务） |

## 已删除 / 退役（历史）

- `novaic-runtime-orchestrator` — 职责已拆分。
- `novaic-tools-server` — 工具执行由 Agent-Runtime + Cortex 接管（若脚本仍出现 `tools` 部署名，需与当前仓库状态一致）。

## 父仓库顶层

```
deploy, docs/, scripts/, .gitmodules, HANDOVER.md, 各 novaic-* 子目录
```
