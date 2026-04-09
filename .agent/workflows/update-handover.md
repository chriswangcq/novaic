---
description: 当 context 即将超限时，将本次对话的关键变更 summarize 到 HANDOVER.md 和对应的 docs/ 架构拆页中
---

## 触发时机

当对话上下文即将超过可用长度时（被系统截断前），执行此 workflow 保存上下文。
由于我们启用了全新的 `docs/` 架构拆页文档系统，记录变迁除了更新日志外，还要负责文档库的保鲜。

## 执行步骤

### 1. 回顾本次对话做了什么

在脑中列出本次对话的所有工作项，分为：
- **代码变更**：改了哪些文件/模块，为什么改
- **架构决策**：做了什么选择，为什么（这是最重要的，下次 AI 续接需要知道）
- **运维操作**：部署了什么，服务器做了什么变更
- **未完成的工作**：下一步该做什么

### 2. 获取变更范围

// turbo
```bash
cd /Users/wangchaoqun/new-build-novaic
git log --oneline -10 2>/dev/null || echo "shallow clone"
```

### 3. 追加 HANDOVER.md (核心日记本)

使用 `multi_replace_file_content` 精确修改 `HANDOVER.md` 的变更日志区（**不要覆盖全文**）。

**必须更新：**
在 `## 三、大版本更新与系统重构交接日志 (Changelogs)` 的下方，立刻追加最新的日志条目：
`> 最后更新：YYYY-MM-DD — **[变更简题]**：这里写一到两句话的本次对话架构调整或者业务增加摘要。`

*注：HANDOVER.md 经过超级瘦身，现在纯粹是一本附带快速部署指令的历史日志。不要把重型的架构分析贴在里面！*

### 4. 同步更新 `docs/` 深度剖析文档 (按需发散)

如果在本次谈话中，你改动了涉及底层或者具体模块逻辑的工作。
**必须**去对应的 `docs/` 包下寻找关联文件，运用 `replace_file_content` 把你做的行为也更新进去以免文档过期：

| 变更发生模块 | 应检视文档区 |
|---|---|
| 网关路由、权限、Hook、AppWS | `docs/gateway/` |
| 聊天同步、SQLite机制、Rust_Cache | `docs/entangled/` (协议层) 和 `docs/frontend/` (客户端渲染) |
| 工作流 Saga、去重、LLM Prompt | `docs/runtime/` |
| WebRTC 管线、硬件截屏、剪切板 | `docs/vmcontrol/` |
| S3 文件转码、CDN | `docs/storage/` 或 `docs/network/` |
| 浏览器自动化、MCP、QEMU | `docs/mcp-vmuse/` |
| 新加接口、环境变量调整 | `docs/README.md` (或附录 runbooks) |

### 5. 提交子架构环境 (Submodule First Commit)

**必须先提交子 repo，再提交主 repo**（否则主 repo 的 submodule 指针无处指向）。

检查哪些子 repo 有未提交变更：
// turbo
```bash
cd /Users/wangchaoqun/new-build-novaic
git submodule foreach 'git status --short | grep -q "." && echo "$name has changes" || true'
```

对每个有变更的子 repo 依次 commit + push：
```bash
# 示例（按实际变更的子 repo 操作）
cd /Users/wangchaoqun/new-build-novaic/novaic-gateway
git add -A
git commit -m "chore: [描述本次变更]"
git push
```

### 6. 归档主仓库 (Master Repo Commit)

```bash
cd /Users/wangchaoqun/new-build-novaic
git add HANDOVER.md docs/
git add novaic-gateway Entangled novaic-app  # 更新 submodule 指针（只加刚才有变更的）
git commit -m "docs/chore: update HANDOVER & sub-pointers — [本次对话总结]"
git push
```

## 纪律提醒
- **子 repo 必须先 push，主 repo 后 push**，顺序绝不能错。
- **文档优先**：代码是给机器跑的，`docs/` 和 `HANDOVER` 才是我们心智延续和对接人类程序员的桥梁。永远保持你的改动在关机前被书面承认。
