---
description: 当 context 即将超限时，将本次对话的关键变更 summarize 到 HANDOVER.md
---

## 触发时机

当对话上下文即将超过可用长度时（被系统截断前），执行此 workflow 保存上下文。

## 执行步骤

### 1. 回顾本次对话做了什么

在脑中列出本次对话的所有工作项，分为：
- **代码变更**：改了哪些文件/模块，为什么改
- **架构决策**：做了什么选择，为什么（这是最重要的，下次 AI 需要知道）
- **部署操作**：部署了什么，服务器做了什么变更
- **未完成的工作**：做到哪一步了，下一步该做什么

### 2. 获取变更范围

// turbo
```bash
cd /Users/wangchaoqun/new-build-novaic
git log --oneline -10 2>/dev/null || echo "shallow clone"
```

### 3. 读取 HANDOVER.md 并检查章节结构

读取 HANDOVER.md，用 `grep -n "^## " HANDOVER.md` 确认当前章节编号，避免引用错误的编号。

// turbo

### 4. 精确更新 HANDOVER.md

使用 `multi_replace_file_content` 精确修改（**不要覆盖全文**）。

**必须更新：**
- 第 3 行：`> 最后更新：YYYY-MM-DD（简要摘要）`

**按需更新（有变更才改，先检查是否本次对话已经更新过）：**

| 变更类型 | 更新章节 |
|---|---|
| 架构/模块变更 | 一、项目整体架构 |
| 仓库结构/submodule | 二、代码仓库说明 |
| 构建/部署流程 | 四/五/六 相关章节 |
| 前端组件/布局 | 九、前端关键文件 |
| iOS 原生改动 | 四、iOS 缩放与键盘行为 |
| 新 bug 修复 | 十三、常见问题（表格末尾追加） |
| 完成了 TODO | 十五、待办（标记 [x] 或删除） |
| 新增 TODO | 十五、待办（追加） |
| 服务器变更 | 十三 末尾「服务器数据维护」 |

**写作原则：**
- 写 **决策和原因**，不只是"改了 X 文件"
- 写 **当前状态**，不只是"做了 Y 操作"
- 如果有未完成的工作，在 TODO 写清楚进度和下一步
- submodule 的变更也要记录

**清理规则：**
- 删除超过 2 周的已完成 TODO
- 不删除没受影响的章节

### 5. 提交所有子仓库和主仓库到 GitHub

先提交所有有变更的子仓库（submodule），再提交主仓库。一条命令完成全部操作。

// turbo-all

**5a. 检查哪些子仓库有变更：**

```bash
cd /Users/wangchaoqun/new-build-novaic
git submodule foreach --quiet 'if [ -n "$(git status --porcelain)" ]; then echo "$sm_path"; fi'
```

**5b. 提交所有有变更的子仓库（每个子仓库执行 add + commit + push）：**

```bash
cd /Users/wangchaoqun/new-build-novaic
SUMMARY="本次对话的一句话总结"
git submodule foreach --quiet '
  if [ -n "$(git status --porcelain)" ]; then
    echo "▸ 提交子仓库: $sm_path"
    git add -A
    git commit -m "chore: '"$SUMMARY"'"
    git push
  fi
'
```

> ⚠️ **注意**：`$SUMMARY` 需要替换为本次对话的实际一句话总结，不能用占位符。

**5c. 提交主仓库（包含 submodule 指针更新 + HANDOVER.md）：**

```bash
cd /Users/wangchaoqun/new-build-novaic
git add -A
git commit -m "docs: update HANDOVER.md — $SUMMARY"
git push
```

> 如果子仓库有新 commit，主仓库的 `git add -A` 会自动包含 submodule 指针变更。

## 注意事项

- HANDOVER.md 是给 **下一次对话的 AI** 看的
- 如果本次对话中已经多次更新过 HANDOVER.md，只需补充遗漏的部分
- commit message 中写清楚本次对话做了什么（Session summary）
- **必须先提交子仓库再提交主仓库**，否则主仓库会引用本地才有的 submodule commit
- 如果某个子仓库 push 失败（权限/网络），记录失败信息并继续处理其他仓库
