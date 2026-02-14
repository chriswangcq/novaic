# NovAIC 技术负责人交接手册

> 本手册总结了担任 NovAIC 技术负责人的工作方法和项目理解，供后续 Agent 接手时参考。

## 目录

1. [项目架构理解](#1-项目架构理解)
2. [任务分配原则](#2-任务分配原则)
3. [调试方法论](#3-调试方法论)
4. [代码修改原则](#4-代码修改原则)
5. [与用户协作](#5-与用户协作)
6. [验证和复查机制](#6-验证和复查机制)
7. [问题定位：先调 API](#7-问题定位先调-api)
8. [理解用户描述 vs 实际根因](#8-理解用户描述-vs-实际根因)
9. [dev-guide 文档使用](#9-dev-guide-文档使用)
10. [Build 验证流程](#10-build-验证流程)
11. [常见踩坑点](#11-常见踩坑点)
12. [快速上手 Checklist](#12-快速上手-checklist)

### 专题文档

- [前端滚动逻辑和虚拟列表](./frontend-scroll-patterns.md) - 虚拟列表、自动滚动、边界条件处理
- [系统稳定性与连接管理](./system-stability-and-connection-management.md) - 长连接 vs 按需连接、QMP 重构案例
- [数据一致性与级联删除](./data-consistency-and-cascade-deletion.md) - 外键约束、孤立数据清理、删除最佳实践
- [架构重构方法论](./architecture-refactoring-methodology.md) - 问题诊断、对比学习、渐进式重构、用户体验设计
- [Saga 与 SubAgent 调试经验](./saga-subagent-debugging.md) - 消息驱动架构调试、Watchdog 排查、SubAgent 通信、工具开发

---

## 1. 项目架构理解

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        NovAIC App                           │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript + Tauri)                      │
│  - novaic-app/src/                                          │
├─────────────────────────────────────────────────────────────┤
│  Gateway (FastAPI) - 端口 19999                             │
│  - novaic-backend/main_gateway.py                           │
│  - novaic-backend/gateway/                                  │
├─────────────────────────────────────────────────────────────┤
│  Task Queue (Worker 进程)                                   │
│  - novaic-backend/task_queue/handlers/                      │
│  - novaic-backend/sagas/                                    │
├─────────────────────────────────────────────────────────────┤
│  Tools Server - 端口 19998                                  │
│  - novaic-backend/tools_server/                             │
├─────────────────────────────────────────────────────────────┤
│  SQLite Database                                            │
│  - ~/Library/Application Support/com.novaic.app/novaic.db   │
└─────────────────────────────────────────────────────────────┘
```

### 数据流：用户消息 → AI 回复

```
用户发送消息
    ↓
Frontend POST /api/chat/send
    ↓
Gateway 写入 chat_messages 表 (status=sending)
    ↓
Watchdog 检测到新消息，创建 Saga
    ↓
Saga Worker 执行 react_think saga
    ↓
Task Worker 执行 llm.call 任务
    ↓
LLM 返回结果
    ↓
Agent 调用 chat_reply 工具
    ↓
Gateway 写入 AGENT_REPLY 消息 + SSE 推送
    ↓
Frontend 收到 SSE，显示回复
```

### 关键目录说明

| 目录 | 说明 |
|------|------|
| `novaic-app/src/store/` | 前端状态管理（Zustand） |
| `novaic-app/src/services/api.ts` | 前端 API 调用 |
| `novaic-app/src/components/` | React 组件 |
| `novaic-backend/main_gateway.py` | Gateway 主文件，所有 HTTP API |
| `novaic-backend/gateway/db/` | 数据库 schema 和 repository |
| `novaic-backend/gateway/api/` | 内部 API（/internal/*） |
| `novaic-backend/task_queue/handlers/` | Task 处理器（llm_handlers, tool_handlers） |
| `novaic-backend/sagas/` | Saga 定义（react_think 等） |
| `novaic-backend/watchdog/` | 消息监控，触发 Saga |

---

## 2. 任务分配原则

### 何时派 subagent，何时自己做

| 场景 | 决策 |
|------|------|
| 读取文件了解情况 | 可以自己做 |
| 修改代码 | **必须派 subagent** |
| 执行 shell 命令 | **必须派 subagent** |
| 简单的 grep/glob 搜索 | 可以自己做 |
| 复杂的调试排查 | 派 subagent |

**重要原则**：用户明确说过"不要自己干活，派 subagent"。

### 如何拆分任务

**按层次拆分**（推荐用于大型迭代）：
- 后端数据层（schema + repository）
- 后端 API 层（gateway endpoints）
- 后端 Worker 层（handlers）
- 前端（types + api + store + components）

**按功能拆分**（推荐用于 bug 修复）：
- 每个独立的 bug 一个 subagent

### 并行 vs 串行

**可以并行**：
- 不同层次的修改（后端 schema 和前端 types 可以并行）
- 不同文件的独立修改
- 最多同时 4 个 subagent

**必须串行**：
- 有依赖关系的修改（repository 依赖 schema）
- 需要前一步结果才能进行的操作

### subagent 类型选择

| 类型 | 适用场景 |
|------|----------|
| `generalPurpose` | 代码修改、复杂调试、需要读写文件 |
| `shell` | 执行命令、build、git 操作 |
| `explore` | 快速搜索代码、了解代码结构 |

### 派活时指定参考文档

**必须告诉 subagent 参考 `dev-guide/` 下的相关文档**：

| 任务类型 | 指定参考文档 |
|----------|--------------|
| 调试问题 | `dev-guide/debugging-guide.md` |
| 修改前后端交互 | `dev-guide/frontend-backend-interaction.md` |
| 修改 Execute Log | `dev-guide/execute-log-flow.md` |
| Build 项目 | `dev-guide/build-process.md` |
| 冒烟测试 | `dev-guide/smoke-test.md` |

### 任务描述模板

**重要**：派活时必须告诉 subagent 参考 `dev-guide/` 目录下的文档！

```
你需要 [做什么]。

**请先阅读 `dev-guide/xxx.md` 了解相关背景。**

## 问题描述
[具体问题]

## 排查/修改方向
1. [步骤1]
2. [步骤2]

## 相关文件
- `path/to/file1.py`
- `path/to/file2.ts`

## 注意事项
- [注意点1]
- [注意点2]
```

---

## 3. 调试方法论

### 数据库和日志位置

```bash
# 数据库
~/Library/Application Support/com.novaic.app/novaic.db

# 日志
~/Library/Application Support/com.novaic.app/*.log
```

### 常用调试命令

```bash
# 查看消息
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, type, content, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT 10;"

# 查看任务队列
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, topic, status, error FROM tasks ORDER BY created_at DESC LIMIT 10;"

# 查看 Saga 状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, saga_type, status, current_step, error FROM sagas ORDER BY created_at DESC LIMIT 5;"

# 查看执行日志
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, kind, status, event_key, timestamp FROM execution_logs ORDER BY id DESC LIMIT 10;"

# 查看应用日志
cat ~/Library/Application\ Support/com.novaic.app/*.log | tail -100

# 调用 API 验证
curl -s "http://127.0.0.1:19999/api/agents" | python3 -m json.tool
curl -s "http://127.0.0.1:19999/api/chat/history?agent_id=xxx&limit=10" | python3 -m json.tool
```

### 问题定位流程

```
用户报告问题
    ↓
1. 先调 API 验证后端数据是否正确
    ↓
2. 如果 API 返回正确 → 前端问题
   如果 API 返回错误 → 后端问题
    ↓
3. 后端问题：检查 Gateway → Repository → Database
   前端问题：检查 Store → API 调用 → 组件渲染
    ↓
4. 查看日志和数据库确认
    ↓
5. 定位到具体函数/文件
```

---

## 4. 代码修改原则

### 接口一致性检查

修改涉及多个文件时，必须检查：

| 调用方 | 被调用方 | 检查点 |
|--------|----------|--------|
| Gateway API | Repository 方法 | 参数名、参数顺序 |
| Worker handler | Gateway client | 参数名、字段名 |
| 前端 API | 后端 endpoint | 字段名、返回格式 |
| 前端 Store | 前端 API | 类型定义一致 |

### 常见接口不一致问题

```python
# 问题：参数名不匹配
# Gateway 调用
repo.upsert_execution_log(input=data)  # ❌
# Repository 签名
def upsert_execution_log(input_data=None)  # 参数名是 input_data

# 修复
repo.upsert_execution_log(input_data=data)  # ✅
```

### 向后兼容

- 新增字段使用可选参数 + 默认值
- 不要删除正在使用的字段
- API 返回值只增不减

### 修改后必须验证

1. **类型检查**：TypeScript 是否报错
2. **API 调用**：curl 验证返回值
3. **数据库**：数据是否正确写入
4. **Build**：能否编译通过

---

## 5. 与用户协作

### 汇报风格

**简洁、表格化、重点突出**：

```markdown
## 问题 1：xxx
**原因**：xxx
**修复**：xxx

## 问题 2：xxx
**原因**：xxx
**修复**：xxx
```

### 何时需要用户确认

- 大型架构改动前
- 不确定需求时
- 有多个方案可选时

### 关键原则

1. **不要自己动手执行命令**，派 subagent
2. **不要猜测**，先调查清楚再行动
3. **及时汇报**，但不要啰嗦

---

## 6. 验证和复查机制

### subagent 结果不能盲信

今天的教训：subagent 说"修好了"，但实际：
- 最后一条消息不显示 → 修了两次才真正解决
- Execute Log 不更新 → 修了两次才真正解决

### 验证方法

1. **让 subagent 验证**：在任务描述中要求"修复后验证"
2. **自己调 API 验证**：curl 调后端 API 检查返回值
3. **让 subagent build 验证**：修改后立即 build

### 复查 Checklist

- [ ] API 返回值是否正确
- [ ] 数据库数据是否正确
- [ ] Build 是否通过
- [ ] 功能是否真正修复

---

## 7. 问题定位：先调 API

### 核心原则

**用户说前端问题，不一定是前端问题。先调 API 验证！**

### 实际案例

用户报告："刷新后消息消失"

```bash
# 步骤 1：调 API 看返回值
curl -s "http://127.0.0.1:19999/api/chat/history?agent_id=xxx&limit=10"

# 发现：API 返回的最后一条是用户消息，缺少 AI 回复

# 步骤 2：查数据库
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db \
  "SELECT id, type, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT 5;"

# 发现：数据库里有 AI 回复

# 结论：问题在后端 API，不是前端
```

### API 调试命令模板

```bash
# 获取 agent 列表
curl -s "http://127.0.0.1:19999/api/agents" | python3 -m json.tool

# 获取消息历史
curl -s "http://127.0.0.1:19999/api/chat/history?agent_id=xxx&limit=20" | python3 -m json.tool

# 获取执行日志
curl -s "http://127.0.0.1:19999/api/logs/entries?agent_id=xxx&limit=20" | python3 -m json.tool
```

---

## 8. 理解用户描述 vs 实际根因

### 常见的描述 vs 根因差异

| 用户描述 | 可能的实际根因 |
|----------|----------------|
| "消息消失" | 存到了错误的 agent |
| "前端过滤" | 后端 API 分页截断 |
| "刷新后不同" | 初始数据加载逻辑问题 |
| "没有更新" | SSE 推送没触发 / API 调用失败 |

### 追问技巧

1. **要求截图**：看具体现象
2. **要求操作步骤**：复现路径
3. **问清楚"之前"和"之后"**：对比差异

### 不要急于修复

1. 先理解问题
2. 调 API / 查数据库验证
3. 确定根因
4. 再派人修复

---

## 9. dev-guide 文档使用

### 重要文档

| 文档 | 用途 |
|------|------|
| `dev-guide/debugging-guide.md` | 调试方法、日志位置、常用命令 |
| `dev-guide/frontend-backend-interaction.md` | 前后端交互流程 |
| `dev-guide/execute-log-flow.md` | Execute Log 数据流 |

### 让 subagent 参考文档

在任务描述中加入：

```
请先阅读 `dev-guide/debugging-guide.md` 了解调试方法。
```

---

## 10. Build 验证流程

### Build 命令

```bash
cd /Users/wangchaoqun/novaic
sh build.sh
```

### 常见 Build 错误

| 错误类型 | 常见原因 |
|----------|----------|
| TypeScript 类型错误 | 类型定义不匹配、可选属性未处理 |
| Python 语法错误 | 缩进、括号不匹配 |
| 导入错误 | 模块路径错误、循环导入 |

### Build 后产物

```
novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app
novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg
```

### Build 验证 Checklist

- [ ] 修改代码后立即派人 build
- [ ] Build 失败立即派人修复
- [ ] 修复后重新 build 验证

---

## 11. 常见踩坑点

### SQLite 特性

**Partial Index 不支持 ON CONFLICT**：
```sql
-- 这样的 partial index 不能用于 upsert
CREATE UNIQUE INDEX idx ON table(a, b, c) WHERE c IS NOT NULL;

-- 必须用普通 unique index
CREATE UNIQUE INDEX idx ON table(a, b, c);
```

**upsert 后 lastrowid 可能为 0**：
```python
# ON CONFLICT DO UPDATE 时 lastrowid 返回 0
# 需要额外查询获取实际 ID
```

### 前端虚拟列表

**不要直接设置 scrollTop**：
```typescript
// ❌ 错误
scrollRef.current.scrollTop = scrollRef.current.scrollHeight;

// ✅ 正确：使用虚拟列表 API
virtualizer.scrollToIndex(messages.length - 1, { align: 'end' });
```

**嵌套滚动容器问题**：
- 只能有一个滚动容器
- 否则虚拟列表计算可见范围会出错

### 分页逻辑陷阱

**reversed + slice 的陷阱**：
```python
# 查询 ORDER BY DESC 得到 [新, 旧]
# reversed 后得到 [旧, 新]
# [:limit] 会截掉最新的！

# 正确做法
messages = all_messages[-limit:] if len(all_messages) > limit else all_messages
```

### 接口参数名

**前端发的 vs 后端收的**：
```python
# 前端发 input_data
# 后端用 log.get("input") 收不到

# 要兼容两种
input_data = log.get("input") or log.get("input_data")
```

---

## 12. 快速上手 Checklist

### 接手后第一步

1. 阅读本手册
2. 阅读 `dev-guide/debugging-guide.md`
3. 阅读 `dev-guide/frontend-backend-interaction.md`

### 必读文件列表

| 文件 | 重要程度 | 说明 |
|------|----------|------|
| `novaic-backend/main_gateway.py` | ⭐⭐⭐ | 所有 HTTP API |
| `novaic-backend/gateway/db/schema.py` | ⭐⭐⭐ | 数据库表结构 |
| `novaic-backend/gateway/db/repositories/chat.py` | ⭐⭐ | 消息和日志存储 |
| `novaic-app/src/store/index.ts` | ⭐⭐⭐ | 前端状态管理 |
| `novaic-app/src/services/api.ts` | ⭐⭐ | 前端 API 调用 |

### 常用命令速查

```bash
# Build
sh build.sh

# 查看数据库
sqlite3 ~/Library/Application\ Support/com.novaic.app/novaic.db

# 调用 API
curl -s "http://127.0.0.1:19999/api/xxx" | python3 -m json.tool

# 查看日志
cat ~/Library/Application\ Support/com.novaic.app/*.log | tail -100
```

### 处理问题的标准流程

```
1. 理解问题（追问细节、要求截图）
     ↓
2. 调 API 验证（curl 检查返回值）
     ↓
3. 查数据库验证（sqlite3 检查数据）
     ↓
4. 定位问题层（前端 or 后端 or 数据库）
     ↓
5. 派 subagent 修复
     ↓
6. 验证修复结果（再次调 API / build）
     ↓
7. 向用户汇报（简洁、表格化）
```

---

## 附录：迭代经验总结

### 2026-02-05：Execute Log 事件模型和多 bug 修复

本手册基于此次迭代经验编写，主要完成了：

1. **Execute Log 事件模型** - 增加 status/kind/event_key/subagent_id 字段
2. **Subagent Tab 切换** - 按 subagent 过滤日志
3. **多个 bug 修复**：
   - 消息存储到错误的 agent
   - 最后一条消息不显示（虚拟列表问题）
   - Execute Log 不更新（SQLite partial index 问题）
   - 分页截断最新消息
   - Model available 状态丢失

期间派出了约 20+ 个 subagent，修复了约 15+ 个 bug。

### 2026-02-05 晚：ExecutionLog 滚动问题深度修复

完成了 ExecutionLog 自动滚动逻辑的全面优化：

1. **滚动问题修复**：
   - 初始滚动"从上滚下来"的问题
   - 翻页后误触发"你有新消息"
   - 自动滚动只在第一次生效的问题
   - 翻页恢复位置误触发的问题
   
2. **UI 布局改进**：
   - 重新设计日志条目布局（时间戳前置、状态右对齐）
   - 详情内容全宽显示，不被时间戳挤压
   - 更清晰的视觉层次

3. **关键教训**：
   - **复杂度是敌人** - 5 个 ref 状态导致 bug 风险指数级增长
   - **边界条件是魔鬼** - "有历史数据时挂载"等边界情况是 bug 温床
   - **慢就是快** - 全面思考清楚再动手比反复调试效率高

详细经验总结见 [前端滚动逻辑和虚拟列表](./frontend-scroll-patterns.md)。

### 2026-02-07：系统稳定性全面提升

完成了多个架构级稳定性问题的诊断与修复：

1. **QMP 连接稳定性**：
   - 问题："Broken pipe" 导致浏览器工具失败
   - 根因：长连接断开后无法恢复
   - 方案：改为按需连接（借鉴 VNC 的成功经验）
   - 效果：自动容错、并发性提升、代码简化

2. **数据一致性问题**：
   - 问题：删除 agent 后残留 501 条消息、2570 条日志
   - 根因：5 个表缺少外键约束
   - 方案：添加外键约束 + 应用层手动清理（双保险）
   - 效果：数据完全清理、级联删除正确

3. **用户体验优化**：
   - 问题：浏览器在虚拟显示运行（DISPLAY=:99），VNC 看不到
   - 根因：理念相悖（用户希望看到 AI 操作）
   - 方案：统一使用 DISPLAY=:0，移除 Xvfb
   - 效果：用户可见 AI 操作，更友好

4. **构建系统陷阱**：
   - 问题：修改代码后 build 不生效
   - 根因：build.sh 条件判断跳过编译
   - 方案：移除条件判断，总是编译（Cargo 增量编译）
   - 效果：确保代码变更生效

5. **前端状态清理**：
   - 问题：删除 agent 后前端残留显示
   - 根因：localStorage 和 SSE 未清理
   - 方案：空列表时自动清空所有状态
   - 效果：状态同步正确

**关键方法论**：
- **对比学习法**：VNC 稳定 → 分析差异 → 借鉴经验修复 QMP
- **渐进式重构**：分阶段迁移多模态标准，每步验证
- **用户体验优先**：技术方案服务用户体验，而非妥协
- **简单胜过复杂**：按需连接 > 长连接+重连、总是编译 > 条件判断

详细经验总结见新增的三个专题文档：
- [系统稳定性与连接管理](./system-stability-and-connection-management.md)
- [数据一致性与级联删除](./data-consistency-and-cascade-deletion.md)
- [架构重构方法论](./architecture-refactoring-methodology.md)

### 2026-02-13：SubAgent 通信机制完善

完成了 SubAgent 通信机制的调试和 `subagent_report` 工具的开发：

1. **SUBAGENT_COMPLETED 消息处理修复**：
   - 问题：Sub SubAgent 完成后，Main Agent 没有被唤醒
   - 根因：Watchdog 不处理 `SUBAGENT_COMPLETED` 消息类型
   - 修复：在 `watchdog.py` 中添加 `_create_subagent_completed_saga` 方法
   - 教训：新增消息类型时必须同步更新 Watchdog

2. **消息初始状态修复**：
   - 问题：`create_message` API 所有消息都用 `status=sent`
   - 根因：需要 Watchdog 处理的消息应该用 `status=sending`
   - 修复：根据消息类型设置正确的初始状态

3. **subagent_report 工具开发**：
   - 功能：让 Sub SubAgent 主动汇报执行结果
   - 设计：只允许 Sub SubAgent 调用，覆盖写入，保留兜底逻辑
   - 实现：Gateway API + Tools Server + System Prompt 指引

4. **调试方法论**：
   - 追踪消息状态流转（sending → sent）
   - 检查 Watchdog 日志（Unknown message type）
   - 验证 Saga 创建和执行
   - 查看 Runtime context 中的 tool_call

**关键教训**：
- **消息驱动架构调试**：从消息状态开始追踪，Watchdog 日志是关键
- **新增消息类型**：必须同时更新 Watchdog 处理逻辑和消息初始状态
- **工具开发流程**：Gateway API → Repository → Tools Server → System Prompt → 端到端测试

详细经验总结见：[Saga 与 SubAgent 调试经验](./saga-subagent-debugging.md)

---

*最后更新：2026-02-13*
