---
description: 当 context 即将超限时，将本次对话的关键变更 summarize 到 HANDOVER.md
---

## 触发时机

当对话上下文即将超过可用长度时（被系统截断前），执行此 workflow 保存上下文。

## 执行步骤

1. 读取当前 `HANDOVER.md` 全文

2. 运行以下命令获取本次变更范围：
```bash
cd /Users/wangchaoqun/new-build-novaic
git diff HEAD~3..HEAD --stat         # 最近几次 commit 的变更文件
git log --oneline -5                  # 最近 commit 消息
```
// turbo

3. 根据本次对话中的工作内容，更新 HANDOVER.md：

   **必须更新的部分：**
   - 第 3 行：更新 "最后更新" 日期和摘要
   - 修正所有 `docs/` 路径引用（文档已分类到 `docs/design/`、`docs/vnc/` 等子目录）

   **按需更新的部分（有变更才改）：**
   - 如果改了架构/新增了模块 → 更新「一、项目整体架构」
   - 如果改了仓库结构/submodule → 更新「二、代码仓库说明」
   - 如果改了构建/部署流程 → 更新「四、构建与发布」或「五、云端部署」
   - 如果改了前端组件/布局 → 更新「八、前端关键文件」
   - 如果改了 iOS 原生 → 更新「四、iOS 部署流程」→「iOS 缩放与键盘行为」
   - 如果修了 bug → 在「十二、常见问题」表格末尾追加
   - 如果完成了 TODO → 在「十四、待办」中标记 [x]

   **清理规则：**
   - 删除超过 2 周的已完成 TODO（标记 [x] 的）
   - 不要删除任何没有受影响的章节
   - 不要重写整个文件，只改变更相关的部分

4. 写回 HANDOVER.md（使用 multi_replace_file_content 精确修改，不要覆盖全文）

5. commit 并 push：
```bash
cd /Users/wangchaoqun/new-build-novaic
git add HANDOVER.md
git commit -m "docs: update HANDOVER.md — [简要说明本次对话做了什么]"
git push origin main:new-build
```

## 注意事项

- HANDOVER.md 是给**下一次对话的 AI** 看的，所以要写清楚：改了什么、为什么改、当前状态、下一步该做什么
- 重点写 **决策和原因**，不只是列代码变更
- 如果有未完成的工作，在 TODO 区域明确标注当前进度和下一步
- submodule 的变更也要包含（novaic-app 等子仓库的改动）
