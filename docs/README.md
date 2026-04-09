# NovAIC 文档（父仓库）

父仓库 **`docs/`** 在 2026-04 重建：**以代码与子模块为真**。本目录从根目录 **`HANDOVER.md`** 抽取可维护的纲要页；**HANDOVER 仍为全文、版本记录与最深细节**。

## 从哪里读起

| 你想… | 建议入口 |
|--------|----------|
| 5 分钟了解组件与端口 | [`architecture/overview.md`](architecture/overview.md) |
| 本地跑前端 / 后端 | [`runbooks/local-dev.md`](runbooks/local-dev.md)、[`runbooks/local-backends.md`](runbooks/local-backends.md) |
| 部署 / 生产主机 | [`runbooks/deploy.md`](runbooks/deploy.md)、[`runbooks/cloud-production.md`](runbooks/cloud-production.md) |
| 排障 | [`runbooks/troubleshooting.md`](runbooks/troubleshooting.md) |
| 子模块清单 | [`reference/submodules.md`](reference/submodules.md) |

## 架构（L1–L2）

| 文档 | 内容 |
|------|------|
| [architecture/overview.md](architecture/overview.md) | 拓扑图、端口表、submodule 表、**文档地图** |
| [architecture/thin-client-and-topology.md](architecture/thin-client-and-topology.md) | OTA 薄壳、云端拓扑、TURN、macOS 键盘 |
| [architecture/authentication.md](architecture/authentication.md) | JWT、Nginx、`deps.py` 环境变量 |
| [architecture/webrtc.md](architecture/webrtc.md) | 远程桌面 WebRTC、VmControl 路由 |
| [architecture/realtime-sync.md](architecture/realtime-sync.md) | App WS、Push、Entangled 与 Sync Contract 索引 |
| [architecture/data-ownership.md](architecture/data-ownership.md) | Entangled vs gateway.db（v63） |
| [architecture/agent-pipeline.md](architecture/agent-pipeline.md) | Saga、ReactThink、工具、LLM Factory |
| [architecture/cortex.md](architecture/cortex.md) | Cortex、DFS Step Tree、部署摘要 |
| [architecture/app-ui.md](architecture/app-ui.md) | 前端 Path C、路由、codegen |

## 参考（配置与周边）

| 文档 | 内容 |
|------|------|
| [reference/submodules.md](reference/submodules.md) | `.gitmodules` 对照、目录说明 |
| [reference/config-and-environment.md](reference/config-and-environment.md) | 本地数据目录、前端 config、Gateway env |
| [reference/file-service.md](reference/file-service.md) | `/api/files/`、语音录制（cpal） |

## Runbooks（可执行）

| 文档 | 内容 |
|------|------|
| [runbooks/local-dev.md](runbooks/local-dev.md) | `npm run dev` / `tauri:dev` |
| [runbooks/local-backends.md](runbooks/local-backends.md) | `start-all.sh`、`start-backends.sh` |
| [runbooks/deploy.md](runbooks/deploy.md) | `./deploy` 命令表 |
| [runbooks/build-and-release.md](runbooks/build-and-release.md) | 桌面/iOS/Android 构建要点 |
| [runbooks/cloud-production.md](runbooks/cloud-production.md) | rsync、`start.sh`、主机路径摘要 |
| [runbooks/troubleshooting.md](runbooks/troubleshooting.md) | 常见问题表 |

## 历史 `docs/` 与删除前快照

重写前正文中的 **`docs/...` 路径** 索引：[historical-doc-links.md](historical-doc-links.md)。

恢复整树：

```bash
git checkout docs-pre-full-rewrite-2026-04-09 -- docs/
```

## 阅读层级（简）

| 层级 | 说明 |
|------|------|
| **L0** | 本页 |
| **L1** | `architecture/overview.md` |
| **L2** | runbooks / reference 单页 |
| **L3** | 各 submodule `README` 与 `docs/`；**`HANDOVER.md`** 全文 |
