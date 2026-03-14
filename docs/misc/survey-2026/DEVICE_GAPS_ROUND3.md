# Device 管理缺口与改进建议（Round 3）

**产出日期**：2026-03-12  
**输入**：`DEVICE_MANAGEMENT_ROUND1.md`、`DEVICE_STATUS_MULTIPC_ROUND2.md`、`DEVICE_FLOATING_PANEL_ROUND2.md`  
**目标**：基于 R1/R2 输出，产出深层缺口分析、多 PC 边界情况、优先级化改进建议

---

## 1. 缺口（深层分析）

### 1.1 deviceMode 未接入

| 维度 | 现状 | 影响 |
|------|------|------|
| **实现状态** | DeviceFloatingPanel 已实现 deviceMode 能力（`useDeviceVncTarget`、`syntheticBinding`、`onStartVm` 等） | 能力闲置 |
| **调用方** | ChatPanel 仅传 `compact`，无 `deviceMode`；LayoutContainer、AgentDrawer、DeviceManagerPage 均不传 | 无入口 |
| **数据流** | deviceMode 时：`useDeviceVncTarget(deviceId, subjectType, subjectId)` → 纯 Device 体系，不依赖 Agent | 已就绪 |

**深层问题**：

1. **DeviceManagerPage 与 DeviceFloatingPanel 割裂**  
   - DeviceManagerPage 使用 `DeviceVNCView`/`DeviceDesktopView` 全屏展示，不渲染 DeviceFloatingPanel  
   - 用户从 Devices 视图选中设备后，无法获得与 Chat 视图一致的浮层预览体验  
   - 窄屏/移动端场景下，全屏视图与浮层预览的体验差异更大

2. **Devices 视图无浮层入口**  
   - `selectedDeviceId`、`selectedVmUser` 由 AgentDrawer 写入，DeviceManagerPage 读取  
   - DeviceFloatingPanel 不读取这些状态，两者无协作  
   - 潜在协作：在 devices 视图时，将 `deviceMode={{ deviceId, subjectType, subjectId }}` 传入 DeviceFloatingPanel

3. **inline 模式未使用**  
   - DeviceFloatingPanel 支持 `inline` 模式（嵌入布局），当前无任何调用方  
   - 若在 DeviceManagerPage 中嵌入 inline DeviceFloatingPanel，可实现列表 + 预览并存

---

### 1.2 useAgentDevice cache 未区分 pc_client_id

| 维度 | 现状 | 影响 |
|------|------|------|
| **Cache key** | `deviceCache.get(deviceId)`，仅用 `deviceId` | 多 PC 同 device 会命中错误缓存 |
| **API 行为** | `api.devices.get(deviceId)` 可能支持 `pc_client_id` 参数（需确认 Gateway） | 若支持，当前未传入 |
| **使用方** | AgentDesktopView、VisualPanel、AgentDrawer（Devices 列表高亮） | 多 PC 场景下 VncTarget.pcClientId 可能错误 |

**深层问题**：

1. **缓存污染**  
   - 用户 A 在 PC-1 上查看 Agent 绑定设备 → `getDeviceCached(deviceId)` 返回 `device.pc_client_id = "pc-1"`  
   - 30s 内用户 B 在 PC-2 上查看同一 Agent 绑定设备 → 命中缓存，得到 `pc_client_id = "pc-1"`  
   - VNC 连接会错误地路由到 PC-1 而非 PC-2

2. **Binding 与 Device 的 pc_client_id 来源不一致**  
   - `getAgentBinding` 返回的 binding 无 `pc_client_id`  
   - `pc_client_id` 完全依赖 `devices.get` 返回的 device  
   - 若 device 缓存错误，整个 VncTarget 的 pcClientId 错误

3. **getDeviceCached 签名缺失**  
   - 当前 `getDeviceCached(deviceId: string)` 无 `pcClientId` 参数  
   - 即使 `api.devices.get` 支持 `pc_client_id`，也无法传入

---

### 1.3 轮询无统一入口

| 维度 | 现状 | 影响 |
|------|------|------|
| **调用方** | DeviceManagerPage、DeviceFloatingPanel、AgentDrawer 各自调用 `useDeviceStatusPolling` | 三处独立 effect |
| **数据源** | 各自传入 `devices`：listForUser、binding/VncTarget、listForUser | 重复轮询同一 device |
| **enabled 条件** | `devices.length > 0`、`!!device`、`isOpen && devices.length > 0` | 条件分散，难以统一优化 |

**深层问题**：

1. **重复轮询**  
   - DeviceManagerPage 与 AgentDrawer 均用 `listForUser` 的 devices，当 Drawer 打开时，同一 device 被两处轮询  
   - DeviceFloatingPanel 单独轮询当前 device，与 Page/Drawer 可能重叠  
   - 无去重逻辑，同一 device 可能被多次 `api.devices.status` 调用

2. **无全局订阅模型**  
   - 理想模型：App 级「需要状态的 device 集合」→ 单一轮询循环按需拉取  
   - 现状：各组件「我有哪些 devices」→ 各自启动轮询，写入同一 Store  
   - 无法根据「谁在订阅」动态调整轮询集合与间隔

3. **intervalMs 依赖 vncConnectionCount**  
   - Store 级 `vncConnectionCount`，任一 VNC 连接即全局 3s  
   - 无法按 device 粒度区分「有 VNC 的 device 3s、无 VNC 的 5s」

4. **statusKey 重复实现**  
   - `deviceStatusStore.ts` 与 `useDeviceStatus.ts` 各有一份 `statusKey` 函数  
   - 未来修改需同步两处，易遗漏

---

## 2. 多 PC 场景的边界情况

### 2.1 同一 device 多实例

| 场景 | 描述 | 当前行为 | 风险 |
|------|------|----------|------|
| **Device 在 PC-A 与 PC-B 各有一份** | 同一逻辑 device（如同一 VM 镜像）在两台物理 PC 上运行 | listForUser 应返回两条记录（不同 pc_client_id）或后端聚合 | 若后端返回单条且无 pc_client_id，状态会覆盖 |
| **用户快速切换 PC** | 用户在 PC-A 查看设备，切到 PC-B 再查看 | useAgentDevice 缓存可能返回 PC-A 的 device | VncTarget.pcClientId 错误，VNC 连错 PC |
| **Drawer 与 Page 不同步** | Drawer 在 PC-A 打开，Page 在 PC-B 打开（多标签/多窗口） | 理论上不会发生，同一会话 | 若未来支持多窗口，需考虑 |

### 2.2 pc_client_id 来源与一致性

| 数据源 | pc_client_id 来源 | 多 PC 正确性 |
|--------|-------------------|--------------|
| listForUser | 后端 DB `devices.pc_client_id` | 依赖后端正确填充 |
| devices.get(id) | 同上 | 同上 |
| useAgentDevice cache | 首次请求的 device，无 pc_client_id 区分 | ❌ 可能错误 |
| useDeviceVncTarget | 来自 devices.get，无缓存 | ✅ 正确 |
| useAgentBinding | devices.get(binding.device_id)，无 30s 缓存 | ✅ 正确（若未走 useAgentDevice） |

### 2.3 状态 key 冲突

| 场景 | statusKey | 说明 |
|------|-----------|------|
| 单 PC | `deviceId` | 无 pc_client_id 时 |
| 多 PC | `deviceId:pcClientId` | 有 pc_client_id 时 |
| listForUser 未填充 pc_client_id | `deviceId` | 多 PC 时不同实例状态会互相覆盖 |

**边界**：若后端 `listForUser` 或 `devices.get` 在多 PC 场景下未返回 `pc_client_id`，前端无法正确隔离，需后端保证。

### 2.4 轮询 device 集合不一致

| 组件 | devices 来源 | 多 PC 时 |
|------|--------------|----------|
| DeviceManagerPage | listForUser | 依赖后端返回完整列表（含各 pc_client_id） |
| DeviceFloatingPanel | useAgentBinding / useDeviceVncTarget | 单 device，通常有 pc_client_id |
| AgentDrawer | listForUser | 与 Page 共享 deviceManagerDevices |

**边界**：DeviceFloatingPanel 的 device 来自 `devices.get`，若 listForUser 与 get 的 pc_client_id 不一致（如后端逻辑差异），轮询 key 与展示 key 可能不匹配。

---

## 3. 改进建议（优先级）

### P0（必须修复）

| ID | 建议 | 说明 |
|----|------|------|
| P0-1 | **useAgentDevice cache 区分 pc_client_id** | 将 `getDeviceCached(deviceId)` 改为 `getDeviceCached(deviceId, pcClientId?)`，cache key 用 `statusKey(deviceId, pcClientId)`；若 `api.devices.get` 支持 pc_client_id 参数则传入 |
| P0-2 | **抽离 statusKey 到共享 util** | 在 `utils/deviceStatusKey.ts` 或 `stores/deviceStatusStore.ts` 导出 `statusKey`，`useDeviceStatus` 与 store 内部共用，消除重复实现 |

### P1（高优先级）

| ID | 建议 | 说明 |
|----|------|------|
| P1-1 | **deviceMode 接入 DeviceManagerPage** | 在 devices 视图时，将 `deviceMode={{ deviceId: selectedDeviceId, subjectType, subjectId }}` 传入 DeviceFloatingPanel（通过 LayoutContainer 或 ChatPanel 的兄弟组件）；或直接在 DeviceManagerPage 内渲染 DeviceFloatingPanel inline |
| P1-2 | **轮询统一入口** | 引入 App 级「设备状态订阅」：各组件通过 `useDeviceStatusSubscribe(deviceId, pcClientId?)` 声明需求，单一 `useDeviceStatusPolling` 根据 Store 的订阅集合轮询，去重、按需拉取 |
| P1-3 | **确认 api.devices.get 是否支持 pc_client_id** | 若 Gateway 支持，useAgentDevice 的 getDeviceCached 传入；若不支持，需后端扩展 |

### P2（中优先级）

| ID | 建议 | 说明 |
|----|------|------|
| P2-1 | **按 device 粒度的轮询间隔** | 有 VNC 连接的 device 用 3s，无 VNC 的用 5s，替代当前全局 vncConnectionCount 控制 |
| P2-2 | **inline DeviceFloatingPanel 试点** | 在 DeviceManagerPage 右侧预览区尝试 inline 模式，验证列表 + 浮层预览并存的 UX |
| P2-3 | **后端 listForUser 多 PC 保证** | 文档化要求：多 PC 场景下 listForUser 必须为每个 device 实例返回正确的 pc_client_id |
| P2-4 | **useAgentDevice 与 useAgentBinding 职责边界** | 评估 useAgentDevice 是否可复用 useAgentBinding 的 device 获取逻辑，避免两套缓存策略 |

---

## 4. 实施顺序建议

```
Phase 1（P0）
  P0-1 useAgentDevice cache 修复
  P0-2 statusKey 抽离

Phase 2（P1）
  P1-3 确认 api.devices.get 能力
  P1-1 deviceMode 接入
  P1-2 轮询统一入口（可与 P1-1 并行）

Phase 3（P2）
  按需推进 P2-1～P2-4
```

---

## 5. 相关文件索引

| 文件 | 关联缺口 |
|------|----------|
| `novaic-app/src/hooks/useAgentDevice.ts` | P0-1 cache key |
| `novaic-app/src/stores/deviceStatusStore.ts` | P0-2 statusKey、轮询 |
| `novaic-app/src/hooks/useDeviceStatus.ts` | P0-2 statusKey |
| `novaic-app/src/hooks/useDeviceStatusPolling.ts` | P1-2 轮询入口 |
| `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | P1-1 deviceMode |
| `novaic-app/src/components/VM/DeviceManagerPage.tsx` | P1-1 deviceMode 接入方 |
| `novaic-app/src/components/Chat/ChatPanel.tsx` | DeviceFloatingPanel 当前唯一调用方 |
| `novaic-app/src/components/Layout/AgentDrawer.tsx` | 轮询调用方、selectedDeviceId 写入 |
