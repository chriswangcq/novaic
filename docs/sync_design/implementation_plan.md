# 多端同步与本地缓存 - 技术实现方案

## 1. 数据库结构调整 (IndexedDB)
文件: `novaic-app/src/db/index.ts`

需要修改 `DB_VERSION`，并在 `upgrade` 升级回调中新增表：
- `agents`: 存储所有的 Agent 配置。keyPath设为 `id`。可选地增加一个 index 以用于排序 (如 `updated_at` 或 `name`)。
- `devices`: 存储用户的所有 Device 元数据。keyPath设为 `id`。
- `skills`: 针对 Custom 和 Builtin Skills，增加表做全量缓存。
- `metadata`: 一个新的 KV 表，或者复用现有的 `prefs` 表，以记录各个模块最后同步的时间戳 (`last_sync_time_agents` 等)。

## 2. 新增 Repository 层
位置: `novaic-app/src/db/` 层需要新增两个文件拦截所有 API 直连并增加发布订阅机制。

### agentRepo.ts
- `putAgents(userId: string, agents: Agent[]): Promise<void>` -> 全量/增量写入。
- `deleteAgentLocal(userId: string, agentId: string): Promise<void>` -> 本地软硬删。
- `getAgents(userId: string): Promise<Agent[]>` -> 从 IDB 读全量。
- `getLastSyncTime(userId): Promise<number>` -> 记录差量时间。
使用 `mitt`（参考 `messageSubscription.ts`）发出 `notifyAgentChange()`，让前端 Hook 消费。

### deviceRepo.ts
- 对应实现 `putDevices`, `getDevices` 以及 `notifyDeviceChange()` 事件分发。可以只缓存静态元数据，状态交给原来的 Store 控制。

## 3. Hook 与 State 改造 (以 Agent 为例)

### 3.1 引入 `useAgentsFromDB.ts` (前端视图消费口)
类似 `useMessagesFromDB.ts`：
```typescript
import { useState, useEffect } from 'react';
import { getAgents } from '../db/agentRepo';
import { onAgentChange, offAgentChange } from '../db/agentSubscription';
import { getCachedUser } from '../services/auth';

export function useAgentsFromDB() {
  const [agents, setAgents] = useState([]);
  const user = getCachedUser();

  useEffect(() => {
    if (!user) return;
    const fetch = async () => setAgents(await getAgents(user.user_id));
    fetch(); // 瞬间上屏
    
    // 订阅 DB 事件（当后端覆盖库之后自动更新组件）
    const handler = () => fetch();
    onAgentChange(user.user_id, handler);
    return () => offAgentChange(user.user_id, handler);
  }, [user]);

  return agents;
}
```

### 3.2 改造 `agentService.ts`
将 `loadAgents` (目前是从网关直接覆盖 Zustand state) 拆解并优化：
- **步骤 1**：向后端发起带游标 `updated_after` 的 `api.listAgents` 拉取差异。
- **步骤 2**：合并到 `agentRepo.ts` 中。
- **步骤 3**：调用 `notifyAgentChange()` 触发 UI 重绘。
- **注意**：Zustand 里的 `setAgents` 依然可以保留用于向下兼容，或彻底下放给被订阅的 Hook。

## 4. 后端路由扩充 (增量获取支持)

文件: Gateway 层（如 `gateway/src/routes/...` / Python 后端服务）
1. `GET /api/agents` 接口：允许接收 `?updated_after={timestamp}` 查询参数。
2. 处理逻辑：只 `SELECT * FROM agents WHERE updated_at >= updated_after OR deleted_at >= updated_after`。前端通过检测 `deleted_at` 是否有值，来进行客户端本地的 IndexedDB 对应条目的销毁。

## 5. SSE 通知流机制对齐

前端 `novaic-app/src/application/syncService.ts` 的改造：

需要监听两个新类型的事件：
- `agent.metadata_updated`
- `device.metadata_updated`

在 `connectUserStream` 中：
```typescript
onAgentMetadataUpdated: async (agentId) => {
   // 客户端收到某 Agent 变更通知后，主动发起 API 局部拉取
   try {
     const latestAgent = await api.getAgent(agentId);
     await agentRepo.putAgents(userId, [latestAgent]);
   } catch (e) { ... }
}
```
这也需要后端 `Gateway` 在成功拦截 `[PUT] /api/agents/:id`、`[POST] /api/agents` 接口返回 200 前，主动向连接池 Broadcast 一条极短的 SSE Event。

## 6. 低频静态数据的 TTL 内存锁方案

文件: `novaic-app/src/components/hooks/useSettings.ts` (或者类似负责抽拉 config 的地方)

针对 `getToolCategories()`：
```typescript
let _toolsCache: Categories | null = null;
let _toolsFetcheTime = 0;
const TTL = 1000 * 60 * 15; // 15分钟

export async function fetchToolCategoriesMemoized() {
   if (_toolsCache && Date.now() - _toolsFetcheTime < TTL) {
       return _toolsCache;
   }
   _toolsCache = await api.getToolCategories();
   _toolsFetcheTime = Date.now();
   return _toolsCache;
}
```
把 `SettingsModal.tsx` 里的 `Promise.allSettled([...])` 全部替换为走这一层 Memoized 的封装调用，以此阻断 Modal 开启时的请求洪峰。
