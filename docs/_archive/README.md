# 文档归档区

本目录用于说明 **「原文档」如何被安全归档**，而不是在父仓再复制一份完整 `docs/`（避免体积翻倍、链接双维护）。

## 1. 权威快照：Git 标签

归档的**可复现快照**以 **annotated tag** 为准。打标签前请尽量在**可合并的干净提交**上操作；工作区有大量未提交改动时，仍可先打标签记录「当时 HEAD」，但合并前建议再打一个「重建完成后」的标签对照。

### 建议命令（在仓库根执行）

```bash
# 查看当前提交
git rev-parse HEAD

# 打归档标签（名称可按日期调整）
git tag -a docs-archive-2026-04-09-pre-rebuild -m "Docs snapshot before planned docs/ rebuild; full tree at this commit."

# 推送到远端（若需要团队可见）
git push origin docs-archive-2026-04-09-pre-rebuild
```

**已打标签（本仓库）**：

| Tag | 说明 |
|-----|------|
| `docs-archive-2026-04-09-post-runbooks` | **runbooks 迁移 + 文档工具链** 合并后快照（annotated，指向含该改动的提交） |

```bash
git push origin docs-archive-2026-04-09-post-runbooks
```

### 按标签取回任意文件

```bash
git show docs-archive-2026-04-09-pre-rebuild:docs/README.md
git checkout docs-archive-2026-04-09-pre-rebuild -- docs/design/SYSTEM_DESIGN.md

# 取 runbooks 阶段之后的树，例如：
git show docs-archive-2026-04-09-post-runbooks:docs/runbooks/README.md
```

### 与历史 graveyard tag 的关系

更早的 **`docs-graveyard-p2`** 等 tag 仍可用于找回 **已 hard purge** 的目录（见 `DOCUMENT_AGGRESSIVE_STRATEGY.md` §七、§八）。**本归档 tag** 针对「**当前工作树**上即将被重组的 `docs/`」；二者用途不同。

## 2. 清单文件

同一次快照可在本目录保留 **`MANIFEST-<tag>.txt`**（`docs/**/*.md` 路径列表），便于 diff 与审计。由 `docs/_scripts/snapshot_docs_manifest.sh` 生成（若存在）。

## 3. 重建蓝图

新文档体系的目标结构、迁移顺序与门禁见 **`../NEW_DOCUMENTATION_BLUEPRINT.md`**（与 `NOVAIC_CANONICAL_GUIDE.md`、`README.md` 配合阅读）。
