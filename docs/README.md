# 文档（重建中）

父仓库 **`docs/`** 已**整目录清空**，供团队**依据子模块与代码**重新撰写。

## 恢复删除前的树

删除时的快照已打标签（任选其一，以 `git tag` 实际输出为准）：

- `docs-pre-full-rewrite-2026-04-09` — 删除前最后一次提交上的整树  
- 亦可使用此前归档 tag，例如 `docs-archive-2026-04-09-post-runbooks`

```bash
git checkout docs-pre-full-rewrite-2026-04-09 -- docs/
```

## 重写时建议入口

- 各子模块仓库内 **`README.md`** 与各自 `docs/`（若存在）  
- 仓库根 **`HANDOVER.md`**（正文内旧 `docs/...` 链接需随重写更新）  
- 代码与配置：`novaic-app`、`novaic-gateway`、`novaic-agent-runtime` 等
