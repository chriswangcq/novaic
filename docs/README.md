# NovAIC 文档（父仓库）

父仓库 `**docs/**`：**与当前子模块代码一致** 的维护页；从 `**HANDOVER.md`** 迁出可导航全文。**HANDOVER** 仍保留**变更日志式「最后更新」**与最长历史段落。

## 从哪里读起


| 你想…          | 建议入口                                                                                                                                      |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 组件与端口        | [architecture/overview.md](architecture/overview.md)                                                                                      |
| 本地开发         | [runbooks/local-dev.md](runbooks/local-dev.md)、[local-backends.md](runbooks/local-backends.md)                                            |
| 构建 / 部署 / 生产 | [build-and-release.md](runbooks/build-and-release.md)、[deploy.md](runbooks/deploy.md)、[cloud-production.md](runbooks/cloud-production.md) |
| 排障           | [troubleshooting.md](runbooks/troubleshooting.md)                                                                                         |
| 路线图 / 待办     | [roadmap/technical-debt.md](roadmap/technical-debt.md)、[roadmap/model-entity-refactor.md](roadmap/model-entity-refactor.md)               |


## 架构

| 文档                                                                          | 内容                                |
| --------------------------------------------------------------------------- | --------------------------------- |
| [overview.md](architecture/overview.md)                                     | 拓扑、端口、**文档地图**                    |
| [thin-client-and-topology.md](architecture/thin-client-and-topology.md)     | OTA、拓扑、TURN                       |
| [authentication.md](architecture/authentication.md)                         | JWT、deps                          |
| [webrtc.md](architecture/webrtc.md)                                         | 远程桌面                              |
| [agent-pipeline.md](architecture/agent-pipeline.md)                         | 后端进程、Saga、工具、源码表                  |
| **[cortex-architecture.md](cortex-architecture.md)**                        | Cortex 详细总览（子模块源码级）               |
| **[cortex/README.md](cortex/README.md)**                                    | Cortex 专题（详细设计与组件） |
| **[entangled-architecture.md](entangled-architecture.md)**                  | Entangled 详细总览（全端库重构版）            |
| **[entangled/README.md](entangled/README.md)**                              | Entangled 专题拆解（全栈集成与 Rust Client） |
| **[gateway-architecture.md](gateway-architecture.md)**                      | Gateway 网关详细总览                      |
| **[gateway/README.md](gateway/README.md)**                                  | Gateway 网关专题拆解                     |
| **[runtime-architecture.md](runtime-architecture.md)**                      | Agent Runtime 详细总览                |
| **[runtime/README.md](runtime/README.md)**                                  | Agent Runtime 专题拆解（Watchdog/Saga等）|
| **[frontend-architecture.md](frontend-architecture.md)**                    | Frontend (React) 详细总览             |
| **[frontend/README.md](frontend/README.md)**                                | Frontend 专题拆解 (Zustand/DOM/Virtual)  |
| **[vmcontrol-architecture.md](vmcontrol-architecture.md)**                  | VmControl (Rust 终端引擎) 详细总览              |
| **[vmcontrol/README.md](vmcontrol/README.md)**                              | VmControl 各平台坑防拆解 (Webrtc/Scrcpy/MacOs)|
| **[mcp-vmuse-architecture.md](mcp-vmuse-architecture.md)**                  | MCP VMuse (模型之手) 总览                 |
| **[mcp-vmuse/README.md](mcp-vmuse/README.md)**                              | MCP VMuse 专题                         |
| **[network-architecture.md](network-architecture.md)**                      | 边缘网络与穿透节点总览                        |
| **[network/README.md](network/README.md)**                                  | 网络设施流转拆解                          |
| **[storage-architecture.md](storage-architecture.md)**                      | 独立 File Storage 大件存储转存架构总览        |
| **[common-architecture.md](common-architecture.md)**                        | 跨端共享与契约 (Common) 架构总览             |
| **[common/README.md](common/README.md)**                                    | 共享端口/代码生成字典拆解                     |
| **[entity-data-models.md](architecture/entity-data-models.md)**                 | **大一统核心实体字典全集**（必须掌握的结构基元）   |


## 参考


| 文档                                                               | 内容        |
| ---------------------------------------------------------------- | --------- |
| [submodules.md](reference/submodules.md)                         | 子模块表      |
| [config-and-environment.md](reference/config-and-environment.md) | 路径、env；**Cortex / NOVAIC_CORTEX_*** |
| [file-service.md](reference/file-service.md)                     | 文件 API、语音 |


## Runbooks


| 文档                                                    | 内容                                        |
| ----------------------------------------------------- | ----------------------------------------- |
| [local-dev.md](runbooks/local-dev.md)                 | dev / tauri:dev                           |
| [local-backends.md](runbooks/local-backends.md)       | 本地后端脚本                                    |
| [deploy.md](runbooks/deploy.md)                       | `./deploy` 子命令                            |
| [build-and-release.md](runbooks/build-and-release.md) | 桌面 / iOS 完整 / Android                     |
| [cloud-production.md](runbooks/cloud-production.md)   | §六§七：deploy 原理、Gateway/Relay/Factory、维护命令 |
| **[ci-cd-and-env.md](runbooks/ci-cd-and-env.md)**         | **隐形 Nginx 分流矩阵与部署环境全貌** (高阶运维必看) |
| [troubleshooting.md](runbooks/troubleshooting.md)     | 排障大全表                                     |


## 路线图（规划/债）


| 文档                                                           | 内容          |
| ------------------------------------------------------------ | ----------- |
| [technical-debt.md](roadmap/technical-debt.md)               | 已落地摘要、待办勾选  |
| [model-entity-refactor.md](roadmap/model-entity-refactor.md) | Model 三实体方案 |
| **[claude-code-comparison.md](roadmap/claude-code-comparison.md)** | **Claude Code 对比与迭代优先级** |
| **[gateway-decomposition.md](roadmap/gateway-decomposition.md)** | **Gateway 职责膨胀分析与拆分路线** |


## 历史 `docs/` 索引

[historical-doc-links.md](historical-doc-links.md) · 恢复整树：`git checkout docs-pre-full-rewrite-2026-04-09 -- docs/`

## 阅读层级


| 层级  | 说明                                   |
| --- | ------------------------------------ |
| L0  | 本页                                   |
| L1  | `architecture/overview.md`           |
| L2  | 各 architecture/runbooks/reference 单页 |
| L3  | 子模块 `README`；**HANDOVER.md**（变更史）    |
