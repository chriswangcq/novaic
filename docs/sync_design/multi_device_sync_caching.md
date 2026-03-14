# Tauri 客户端多端同步与本地缓存架构设计

## 1. 背景与核心挑战

随着 Novaic 客户端功能的演进，部分高频数据（Messages, Logs）已经通过 `IndexedDB` 加上 `SSE (Server-Sent Events)` 实现了极速读写与流式同步，体验极佳。

然而，像 **Agents 列表**、**Devices 列表**、**配置选项（Skills / Tool Categories）** 等较为低频变更的基建数据（Data Lists/Metadata），目前仍然极度依赖内存缓存 (`Zustand`) 与组件挂载时的全量高并发 API 请求。这导致了三个核心卡点：
1. **Fetch Waterfall（请求瀑布流）与白屏延迟**：打开 `SettingsModal -> Agent Tools` 时，由于前端未做有效并发控制与缓存，会瞬间发起近 7 个不同的强网络请求。
2. **离线白屏**：若网络不佳或服务异常，Drawer 和列表页没有能支撑展示的后备数据。
3. **多端状态割裂**：当用户在 PC 端新建了一个 Agent 或修改了设置，移动端由于并未及时刷新或缺乏被动通知，显示的依然是旧数据。

## 2. 核心设计原则

为了彻底解决上述体验瓶颈并面向未来支持多端无缝切换，本方案确立三个设计主旨：
1. **SWR 渲染优先 (Stale-While-Revalidate)**：不论何时打开面板，先从 IndexedDB (IDB) 中拿“脏数据”糊满 UI，绝不挂 Loading（除了首次下载应用）。后台静默获取最新数据，再通过状态派发完成无感覆盖。
2. **轻量级通知，重量级校准 (Event Notification > State Push)**：通过 SSE 通道向客户端推送只包含 ID 与 Event Type 的事件，前端通过定向 Fetch 解决脏数据覆盖，杜绝因大量下发报文引起的网卡和内存拥堵，且彻底规避乱序时序问题。
3. **低频配置引入 TTL 时效机制**：对于内置的静态资源或极少变更的列表（如 Built-in Skills），做应用级的全局缓存锁。

## 3. 前端改造架构：缓存分层策略

我们将对不同性质的数据进行两极化的缓存方案治理。

### 3.1 核心列表层：引入 Repo 落盘机制

新增 `agentRepo.ts` 与 `deviceRepo.ts`，利用已有的 `db/index.ts` Dexie 基础。这两者都将直接存入 IndexedDB。

**数据流向（以 AgentList 为例）：**
1. **获取（Read）**:  
   使用 `useAgentsFromDB` Hook 订阅数据库。
   组件加载时，`AgentService.loadAgents()` 会优先从 `agentRepo` getAll 并立即返回给 `Zustand store` 渲染 UI。
2. **更新（Revalidate)**:  
   紧接着静默去调 `api.listAgents({ updated_after: last_sync_time })`。(详见章节 4)。拿到新结果后写入 IDB，由于 `useAgentsFromDB` 的监听，UI 会发生“闪烁更新”变成最新状态。

### 3.2 低频静态源：挂载 TTL (Time To Live)

那些在整个运行时生命周期几乎不变化的元信息（如 `api.getToolCategories()`），不应每次弹窗都获取，也无需沉重到上 IndexedDB。

通过简单的模块作用域实现记忆（Memoize Layer）：
```typescript
let cachedToolCategories: any = null;
let lastFetchTime = 0;
const CACHE_TTL = 1000 * 60 * 15; // 15 分钟

export async function getToolCategoriesConfig() {
  const now = Date.now();
  if (cachedToolCategories && (now - lastFetchTime < CACHE_TTL)) {
    return cachedToolCategories;
  }
  cachedToolCategories = await api.getToolCategories();
  lastFetchTime = now;
  return cachedToolCategories;
}
```

## 4. 后端配合改造：事件驱动多端状态同步 (SSE Sync)

基于当前 `gateway/sse.ts` 和 User Stream 体系的成熟度，多端同步方案只需稍加补充路由支持。

### 4.1 引入元数据 (Metadata) 变更的 SSE 广播
当任何一端（或直接来自 API 调用）成功让后端执行了 `INSERT / UPDATE / DELETE` 操作后，Gateway 需要将其打包为一条 **极简纯指令** 下发到该 `user_id` 的全量 SSE Session：

```json
{
  "event": "agent_metadata_updated",
  "agent_id": "agn_xxx123",
  "action": "updated" // created | updated | deleted
}
```

### 4.2 前端 `syncService.ts` 接入补全数据

前端在 `UserStreamHandlers` 里实现接收。因为我们采取了流派一**“通知级同步”**，所以接收到信号后，Tauri 仅仅发起一次精准的网络请求：

```typescript
// syncService.ts 内的方法扩充
async handleAgentMetadataEvent(event) {
  if (event.action === 'deleted') {
     // 直接删库并通知仓库，Zustand 更新
     await this.agentService.removeAgentLocally(event.agent_id);
  } else {
     // 对于 updated 和 created
     // 精确 Fetch 这个 ID 的全部结构体，覆写本地 IDB，事件驱动 UI。
     await this.agentService.fetchAndMergeAgent(event.agent_id);
  }
}
```

这避免了如果是 A 手机和 B PC 同时乱序操作同一 Agent，A/B 两端数据被冲垮的问题。因为大家最终都会乖乖地拿着 `agent_id` 找 Gateway 进行一次“权威提款”。

### 4.3 离线重连的防丢策略：Delta Sync (增量更新)

为了解决两台设备从未同时在线过的长线同步问题，在全聚合的 List 请求上增加时间游标是非常有必要的（类似于已经实现的 `getChatHistory(updated_after)`）。

对 `listAgents` 等接口增加 `updated_after` 参数支持。

*   当 App 从后台切回前台，判断 SSE 断开，执行 `scheduleReconnect` 成功时。
*   Tauri 获取本地 `agentRepo` 里记录的最后一条更新时间，发去后端请求增量。
*   合并差异部分。这一步也正是 SWR 的核心实现基础。

## 5. 阶段实施计划参考

**Phase 1：快赢 (Quick Wins - SWR 落地)**
*   在 Dexie `db/index` 中创建 `agents` 和 `devices` 表结构。
*   改造现有的 Store (`useAppStore.agents`, `useAppStore.deviceManagerDevices`) 从直连 API 变为直挂到 IDB 订阅。
*   实现无感启动秒开侧边栏。

**Phase 2：砍掉高并发痛点 (Fetch Waterfall 梳理)**
*   梳理 `SettingsModal` 中的 `Promise.allSettled`。
*   针对 `getToolCategories`, `getSkills` 添加 TTL 层锁，只允许 App 会话期内首次打开触发网关拉取，后续读取缓存。

**Phase 3：对接多端体系 (SSE Notification)**
*   后端添加针对 `Agent`/`Device` 的变动派发事件 (Event/Action 推送)。
*   前端 `syncService.ts` 写出对应的 `handle` 函数自动去校验单条权威数据。

---

> 通过这套组合拳（**IDB 加速度 + SWR 补漏口 + Event Notification 平衡流量**），Tauri 客户端不仅可以在长途飞机上展现出完美的无网络容错性，即使多台手机与电脑共存，界面状态也会如倒推多米诺骨牌般丝滑自洽。
