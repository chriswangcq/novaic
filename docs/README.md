# NovAIC 文档（父仓库）

父仓库 **`docs/`**：**与当前子模块代码一致** 的维护页；从 **`HANDOVER.md`** 迁出可导航全文。**HANDOVER** 仍保留**变更日志式「最后更新」**与最长历史段落。

## 从哪里读起

| 你想… | 建议入口 |
|--------|----------|
| 组件与端口 | [architecture/overview.md](architecture/overview.md) |
| 本地开发 | [runbooks/local-dev.md](runbooks/local-dev.md)、[local-backends.md](runbooks/local-backends.md) |
| 构建 / 部署 / 生产 | [build-and-release.md](runbooks/build-and-release.md)、[deploy.md](runbooks/deploy.md)、[cloud-production.md](runbooks/cloud-production.md) |
| 排障 | [troubleshooting.md](runbooks/troubleshooting.md) |
| 路线图 / 待办 | [roadmap/technical-debt.md](roadmap/technical-debt.md)、[roadmap/model-entity-refactor.md](roadmap/model-entity-refactor.md) |

## 架构

| 文档 | 内容 |
|------|------|
| [overview.md](architecture/overview.md) | 拓扑、端口、**文档地图** |
| [thin-client-and-topology.md](architecture/thin-client-and-topology.md) | OTA、拓扑、TURN |
| [authentication.md](architecture/authentication.md) | JWT、deps |
| [webrtc.md](architecture/webrtc.md) | 远程桌面 |
| [realtime-sync.md](architecture/realtime-sync.md) | Push、App WS（摘要） |
| [entangled-store-and-app-ws.md](architecture/entangled-store-and-app-ws.md) | 单 Store、schema push、稳定性（详） |
| [data-ownership.md](architecture/data-ownership.md) | Entangled vs gateway.db v63 |
| [agent-pipeline.md](architecture/agent-pipeline.md) | 后端进程、Saga、工具、源码表 |
| [cortex.md](architecture/cortex.md) | Cortex 全架构（当前） |
| [app-ui.md](architecture/app-ui.md) | 前端 Path C、HTTP→Entangled 表 |

## 参考

| 文档 | 内容 |
|------|------|
| [submodules.md](reference/submodules.md) | 子模块表 |
| [config-and-environment.md](reference/config-and-environment.md) | 路径、env |
| [file-service.md](reference/file-service.md) | 文件 API、语音 |

## Runbooks

| 文档 | 内容 |
|------|------|
| [local-dev.md](runbooks/local-dev.md) | dev / tauri:dev |
| [local-backends.md](runbooks/local-backends.md) | 本地后端脚本 |
| [deploy.md](runbooks/deploy.md) | `./deploy` 子命令 |
| [build-and-release.md](runbooks/build-and-release.md) | 桌面 / iOS 完整 / Android |
| [cloud-production.md](runbooks/cloud-production.md) | §六§七：deploy 原理、Gateway/Relay/Factory、维护命令 |
| [troubleshooting.md](runbooks/troubleshooting.md) | 排障大全表 |

## 路线图（规划/债）

| 文档 | 内容 |
|------|------|
| [technical-debt.md](roadmap/technical-debt.md) | 已落地摘要、待办勾选 |
| [model-entity-refactor.md](roadmap/model-entity-refactor.md) | Model 三实体方案 |

## 历史 `docs/` 索引

[historical-doc-links.md](historical-doc-links.md) · 恢复整树：`git checkout docs-pre-full-rewrite-2026-04-09 -- docs/`

## 阅读层级

| 层级 | 说明 |
|------|------|
| L0 | 本页 |
| L1 | `architecture/overview.md` |
| L2 | 各 architecture/runbooks/reference 单页 |
| L3 | 子模块 `README`；**HANDOVER.md**（变更史） |
