# 端上数据库维护架构

> 端侧 IndexedDB 是唯一事实来源，所有业务逻辑只负责写库，UI 通过订阅自动响应。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流向（单向）                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   用户操作 / SSE 推送                                                         │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│   │ MessageSvc  │     │  LogService │     │  SyncService │                   │
│   │ LogService  │     │             │     │  (SSE 分发)   │                   │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                   │
│          │                   │                   │                           │
│          └───────────────────┼───────────────────┘                           │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Repo 层：messageRepo / logRepo / prefsRepo / fileRepo               │   │
│   │  写库 → notifyMessageChange / notifyLogChange                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  IndexedDB（按 userId 隔离：novaic_local_{userId}）                    │   │
│   │  messages | logs | prefs | files                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              │  notify 触发                                  │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Subscription：messageSubscription / logSubscription                │   │
│   │  订阅者 callback → refetch from DB                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  useMessagesFromDB / useLogsFromDB                                   │   │
│   │  UI 组件只读 DB 查询结果，不直接操作任何 Store                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、IndexedDB Schema

**库名**：`novaic_local_{userId}`（按用户隔离）


| Store        | 主键  | 索引                                                                         | 用途                                      |
| ------------ | --- | -------------------------------------------------------------------------- | --------------------------------------- |
| **messages** | id  | by_agent_ts [agentId, timestamp] by_agent_updated_at [agentId, updated_at] | 对话消息                                    |
| **logs**     | id  | by_agent_id [agent_id, id]                                                 | 执行日志                                    |
| **prefs**    | key | -                                                                          | 偏好：selectedAgent, selectedModel, layout |
| **files**    | id  | -                                                                          | 附件/图片缓存                                 |


---

## 三、核心维护逻辑

### 3.1 消息（messages）


| 场景          | 入口                                                | 写库路径                                                         | 游标                     |
| ----------- | ------------------------------------------------- | ------------------------------------------------------------ | ---------------------- |
| **冷启动加载**   | `MessageService.load(agentId)`                    | `_deltaSync` → gateway.getChatHistory → putMessages          | 从 DB 派生                |
| **增量同步**    | 同上                                                | 有 lastSync 且 7 天内 → updated_after 拉 delta → putMessages      | getLastSyncTime        |
| **用户发送**    | `MessageService.send()`                           | 先 putMessages(乐观) → gateway.sendChatMessage → replaceMessage | 写库即更新                  |
| **SSE 新消息** | `SyncService.onAgentReply` → handleIncoming       | putMessages                                                  | 写库即更新                  |
| **已读回执**    | `SyncService.onStatusUpdate` → handleStatusUpdate | updateMessageRead                                            | 写库即更新                  |
| **加载更多**    | `MessageService.loadMore()`                       | gateway.getChatHistory(before_id) → putMessages              | 写库即更新                  |
| **展开截断**    | `MessageService.expand()`                         | gateway.getChatMessage → putMessages(更新 summary)             | 写库即更新                  |
| **清空**      | `MessageService.clear()`                          | deleteAgentMessages                                          | clearMessagePagination |


**关键点**：

- 所有写库后都会调用 `notifyMessageChange(userId, agentId)`
- `useMessagesFromDB` 订阅该 key，收到通知后 `refetch` 从 DB 拉最新数据
- **同步游标从 DB 派生**：`msgRepo.getLastSyncTime()` 返回该 agent 在 messages 表中的最大 `updated_at`，用于 delta 的 `updated_after`。SSE 新消息、用户发送、已读回执都会写库，游标自动更新，无需单独维护

### 3.2 日志（logs）


| 场景                     | 入口                                        | 写库路径                                 | 游标                 |
| ---------------------- | ----------------------------------------- | ------------------------------------ | ------------------ |
| **冷启动加载**              | `LogService.load(agentId)`                | 只读本地 getLogs，不拉服务端                   | -                  |
| **SSE log_batch**      | `SyncService.onLogBatch` → handleBatch    | putLogs（全量写入，不过滤 subagent）           | 写库即更新              |
| **SSE log_entry**      | `SyncService.onLogEntry` → handleIncoming | putLogs                              | 写库即更新              |
| **logs_updated 事件**    | `SyncService.onLogsUpdated`               | fetchAndMerge（拉服务端增量）→ putLogs       | 写库即更新              |
| **SSE 重连后**            | deltaSync                                 | getLogEntries(after_id) → putLogs    | getMaxLogId        |
| **loadMore**           | `LogService.loadMore()`                   | getLogEntries(before_id) → putLogs   | 不更新（拉的是更早的）        |
| **filterBySubagent**   | `LogService.filterBySubagent()`           | getLogEntries → putLogs              | 写库即更新              |
| **appendSubagentLogs** | 胶囊点击展开子 agent                             | getLogEntries(subagent_id) → putLogs | 写库即更新              |
| **清空**                 | `LogService.clear()`                      | deleteAgentLogs                      | clearLogPagination |


**关键点**：

- 日志**全部写入 DB**，不再按 logSubagentId 过滤；过滤只在**读**时（getLogs 的 subagentId 参数）
- **游标从 DB 派生**：`logRepo.getMaxLogId()` 返回该 agent 在 logs 表中的最大 id，用于 delta 的 `after_id`。与消息一致，无需 prefs 维护

### 3.3 偏好（prefs）


| Key           | 用途          |
| ------------- | ----------- |
| selectedAgent | 上次选中的 agent |
| selectedModel | 上次选中的模型     |
| layout        | 布局偏好        |


> 消息与日志的 delta 游标**均从 DB 派生**：`msgRepo.getLastSyncTime()`（max updated_at）、`logRepo.getMaxLogId()`（max id），不存 prefs。

---

## 四、订阅与 UI 响应

```
messageRepo.putMessages()
    → notifyMessageChange(userId, agentId)
        → 所有 subscribe(userId, agentId) 的 callback 被调用
            → useMessagesFromDB 的 refetch()
                → msgRepo.getMessages() → setMessages()
                    → 组件重渲染
```

- **不传数据**：callback 只负责触发 refetch，数据从 DB 重新查，避免内存里的数据与 DB 不一致
- **refetch 竞态防护**：`refetchVersionRef` + `isCurrent()`，防止旧 refetch 覆盖新结果

---

## 五、多用户与生命周期


| 时机       | 行为                                                        |
| -------- | --------------------------------------------------------- |
| **登录**   | `getDb(userId)` 打开 `novaic_local_{userId}`                |
| **登出**   | `resetDb()` 关闭当前 DB 句柄；`clearMessagePagination` 等清空 Store |
| **切换用户** | 新用户登录时 `_dbUserId !== userId`，会 close 旧 DB 再 open 新库      |


---

## 六、轻量 Store（非 DB）

以下状态**不入 IndexedDB**，仅内存：


| Store                  | 用途                                                       |
| ---------------------- | -------------------------------------------------------- |
| messagePaginationStore | hasMore, isLoading（按 agentId）                            |
| logPaginationStore     | hasMore, isLoading, lastLogId（按 agentId + logSubagentId） |
| logFilterStore         | logSubagentId, logSubagents                              |
| logInputCacheStore     | 展开后的 input 缓存                                            |


原因：属于 UI/拉取元数据，非领域数据；重启后从 DB 重新拉即可。

---

## 七、关键代码路径速查


| 操作          | 文件:函数                                                                                 |
| ----------- | ------------------------------------------------------------------------------------- |
| 消息写库        | `messageRepo.putMessages`                                                             |
| 消息通知        | `messageSubscription.notifyMessageChange`                                             |
| 消息订阅        | `useMessagesFromDB` → `subscribe`                                                     |
| 日志写库        | `logRepo.putLogs`                                                                     |
| 日志通知        | `logSubscription.notifyLogChange`                                                     |
| 消息 delta 游标 | `msgRepo.getLastSyncTime`（从 DB 派生）                                                    |
| 日志 delta 游标 | `logRepo.getMaxLogId`（从 DB 派生）                                                        |
| SSE → 消息    | `syncService.onAgentReply` → `msgService.handleIncoming`                              |
| SSE → 日志    | `syncService.onLogEntry` / `onLogBatch` → `logService.handleIncoming` / `handleBatch` |


