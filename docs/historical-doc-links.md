# 历史文档路径（父仓 `docs/` 重写前）

父仓库曾于 **2026-04** 整目录移除 `docs/`，按代码重写。下列 **`docs/...` 路径** 在旧提交中仍存在，可用 **tag `docs-pre-full-rewrite-2026-04-09`**（或你仓库中同等「删除前快照」tag）查看。

## 通用查看方式

```bash
# 列出 tag（以本地为准）
git tag -l 'docs-*'

# 查看某文件在删除前的内容（分页）
git show docs-pre-full-rewrite-2026-04-09:docs/<路径> | less

# 检出整树到工作区（慎用，会覆盖当前 docs/）
git checkout docs-pre-full-rewrite-2026-04-09 -- docs/
```

**仅归档、不进主文档线的旧稿**（例如 `docs/archived/`）另见 tag **`docs-graveyard-p2`**：

```bash
git show docs-graveyard-p2:docs/archived/
```

## 与 `HANDOVER.md` 交叉引用较多的文件

| 旧路径 | 备注 |
|--------|------|
| `docs/architecture-verification-2026-04.md` | schema / Entangled 与 Gateway 分工等验证笔记 |
| `docs/cortex-architecture.md` | Cortex 总览 |
| `docs/context-assembly-dfs-step-tree.md` | DFS Step Tree 上下文拼装 |
| `docs/design-no-tool-system-message.md` | no-tool / LLM 上下文与工具管线 |
| `docs/SYNC_CONTRACT.md` | Sync Contract 规范 |
| `docs/sync-contract-execution-checklist.md` | 执行清单 |
| `docs/skills-domain-investigation-reports.md` | Skills 领域分报告 |
| `docs/agent-approve-points/02-openclaw-architecture.md` | OpenClaw 对照笔记 |

当前 **L1 架构入口**（重写后）见 [`architecture/overview.md`](architecture/overview.md)。
