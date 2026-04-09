# NovAIC 文档（父仓库）

父仓库 **`docs/`** 在 2026-04 整目录重建：**以代码与子模块为真**；本目录提供 **L0 导航** 与少量 **L1** 概览。历史树可通过 git 恢复（见下）。

## 阅读层级

| 层级 | 内容 | 入口 |
|------|------|------|
| **L0** | 从哪读起、谁拥有哪段真相 | 本页 |
| **L1** | 系统拓扑、端口、submodule 表 | [`architecture/overview.md`](architecture/overview.md) |
| **L2** | 可执行步骤（本地开发等） | [`runbooks/local-dev.md`](runbooks/local-dev.md) |
| **L3** | 深度设计、合约、各域细节 | 各 **submodule** 内 `README.md` / `docs/`，以及根目录 **`HANDOVER.md`** |

## 恢复删除前的 `docs/` 树

```bash
git checkout docs-pre-full-rewrite-2026-04-09 -- docs/
```

（若标签名不同，以 `git tag` 中带 `docs-pre` / `docs-archive` 的为准。）

## Submodule 文档

实现与 API 细节在子模块仓库中维护，例如：

- `novaic-app/` — 客户端、Tauri  
- `novaic-gateway/` — Gateway  
- `novaic-agent-runtime/` — Agent 运行时  
- `novaic-cortex/` — Cortex  
- `novaic-common/config/services.json` — 本地服务端口等约定  

父仓 **`HANDOVER.md`** 仍为总览与运维说明；其中指向旧 `docs/...` 的链接会随本目录补全而逐步修订。
