# 仓库与子模块

> 对应 **`HANDOVER.md` §三**。权威清单：根目录 **`.gitmodules`**。

**文档策略**：架构、API、Runbook **只维护在父仓库 `docs/`**。各子模块 **不维护** `docs/` 文档树，仅保留根目录 **`README.md`**（项目一句说明 + 开发/运行命令）。详细说明以父仓库为准。

```bash
git clone --recurse-submodules git@github.com:chriswangcq/novaic.git
git submodule update --init --recursive
```

## Submodule 一览

| 目录 | 用途 |
|------|------|
| `novaic-app` | Tauri 桌面 + 移动端 |
| `novaic-gateway` | 云端 Gateway |
| `novaic-business` | Business Service（Agent/Skill/Form/Model） |
| `novaic-device` | Device Service（设备 / PC-Bridge WS / VM） |
| `novaic-quic-service` | STUN + Relay |
| `novaic-agent-runtime` | Agent 运行时（Task/Saga/Workers） |
| `novaic-mcp-vmuse` | MCP VMuse |
| `novaic-common` | 共享库与配置（含 `config/services.json`） |
| `novaic-storage-a` | File Service |
| `novaic-cortex` | Cortex HTTP |
| `Entangled` | 同步引擎（Python/Rust 等） |
| `byclaw-website` | 官网 |
| `thirdparty/openclaw` | 上游参考（非线上服务） |

## 父仓库顶层

```
deploy, docs/, scripts/, .gitmodules, HANDOVER.md, 各 novaic-* 子目录
```
