# Device 按 Subject 渲染方案设计

## 1. 背景与目标

### 1.1 现状问题

- `agent.devices` 为空：`DeviceRepository.list_by_agent()` 不存在，`_load_devices_for_agent` 无法填充设备列表
- 正确数据流应为：`getAgentBinding(agentId)` → binding → `api.devices.get(binding.device_id)` → device
- 需要按 binding 的 `subject_type` / `subject_id` 选择正确的渲染组件（main / vm_user / default）

### 1.2 目标

- 基于 agent 的 binding（device + subject）重新渲染 Device 区域
- 复用现有 Tauri App → VmControl 连接链路，不改动底层 VNC/Scrcpy 协议
- 支持 main（主桌面）、vm_user（子用户）、default（Android）三种 subject

---

## 2. 数据模型与 API

### 2.1 Binding 模型

```python
# agent_device_binding
agent_id, device_id, subject_type, subject_id, mounted_tools, ...
# subject_type: 'main' | 'vm_user' | 'default'
# subject_id: main→"main", vm_user→username, default→"default"
```

### 2.2 已有 API（无需新增）

| API | 用途 |
|-----|------|
| `GET /api/agents/{agent_id}/binding` | 获取当前 agent 的 binding |
| `GET /api/devices/{device_id}` | 获取 device 详情 |
| `GET /api/devices/{device_id}/status` | 设备运行状态 |

### 2.3 前端类型（需补充）

```typescript
// 已有
interface AgentDeviceBinding {
  agent_id: string;
  device_id: string;
  subject_type: 'main' | 'vm_user' | 'default';
  subject_id: string;
  device_type?: string;
  device_name?: string;
  subject_label?: string;
  // ...
}
```

---

## 3. 连接链路（保持不变）

```
Tauri App → VmControl → QEMU/ADB (Linux VM / AVD)
         ↑
     Gateway 负责鉴权与 binding 解析
```

- **main**：VNC 使用 `agent_id`，socket 路径 `novaic-vnc-{agent_id}.sock`
- **vm_user**：VNC 使用 `deviceId:username`，port 文件 `/tmp/novaic/share-{device_id}/vnc-{username}.port`
- **default (Android)**：Scrcpy 使用 `device.serial`

---

## 4. 实现方案

### 4.1 数据流改造

**原逻辑（失效）：**
```ts
const devices = currentAgent?.devices || [];  // 始终为空
```

**新逻辑：**
```ts
// 1. 获取 binding
const binding = await api.agents.getBinding(currentAgentId);
if (!binding) return null;

// 2. 获取 device
const device = await api.devices.get(binding.device_id);

// 3. 构造渲染用的 SubjectCard 数据
const subjectCard = {
  device,
  binding,
  key: `${binding.device_id}:${binding.subject_type}:${binding.subject_id}`,
};
```

### 4.2 按 Subject 选择渲染组件

| subject_type | 设备类型 | 渲染组件 | VNC/连接参数 |
|--------------|----------|----------|--------------|
| main | linux | VNCViewShared | agentId（store 的 currentAgentId） |
| vm_user | linux | VmUserVNCView | deviceId, username (subject_id) |
| default | android | ScrcpyView | device.serial |

### 4.3 组件改造清单

#### 4.3.1 DeviceFloatingPanel

| 改造项 | 说明 |
|--------|------|
| 数据源 | 用 `getAgentBinding` + `api.devices.get` 替代 `currentAgent?.devices` |
| 状态轮询 | 对 binding.device_id 调用 `api.devices.status` |
| 渲染单位 | 从「按 device」改为「按 binding（即 device+subject）」 |
| DeviceCard 入参 | 传入 `{ device, binding }` 而非仅 `device` |

#### 4.3.2 DeviceCard

| 改造项 | 说明 |
|--------|------|
| 流组件分支 | 根据 `binding.subject_type` + `device.type` 选择 VNCViewShared / VmUserVNCView / ScrcpyView |
| main | `device.type === 'linux' && subject_type === 'main'` → VNCViewShared（使用 store 的 currentAgentId） |
| vm_user | `device.type === 'linux' && subject_type === 'vm_user'` → VmUserVNCView(deviceId, username) |
| default | `device.type === 'android'` → ScrcpyView(device.serial) |

#### 4.3.3 VNCViewShared

- 保持现状：以 `agentId` 为 key，用于 main 桌面
- 无需支持 vm_user（vm_user 使用 VmUserVNCView）

#### 4.3.4 VmUserVNCView

- 已支持 `deviceId` + `username`，`getVncUrl(\`${deviceId}:${username}\`)`
- 可直接复用，仅需在 DeviceCard 中按 subject 条件渲染

#### 4.3.5 StoppedDeviceChip

- 入参改为 `{ device, binding }`
- 启动逻辑仍为 `api.devices.start(device.id)`
- 展示名称可用 `binding.subject_label` 或 `device.name`

---

## 5. 实现步骤

### Phase 1：数据层

1. 确认 `api.agents.getBinding(agentId)` 已存在且返回 `AgentDeviceBinding`
2. 新增 hook：`useAgentBinding(agentId)` → `{ binding, device, loading, error }`
   - 内部：`getBinding` → `devices.get(binding.device_id)` → 合并返回

### Phase 2：DeviceFloatingPanel 改造

1. 用 `useAgentBinding(currentAgentId)` 替代对 `currentAgent?.devices` 的依赖
2. 当 `binding` 存在时，构造 `SubjectCardInfo[]`（每个元素含 device + binding）
3. 将 `SubjectCardInfo` 传给 DeviceCard / StoppedDeviceChip

### Phase 3：DeviceCard 按 subject 渲染

1. 根据 `binding.subject_type` 和 `device.type` 分支：
   - `main` + linux → `<VNCViewShared />`
   - `vm_user` + linux → `<VmUserVNCView deviceId={device.id} username={binding.subject_id} ... />`
   - `default` + android → `<ScrcpyView deviceSerial={device.serial} ... />`
2. 工具栏、PowerMenu 等逻辑保持不变（仍基于 device.id）

### Phase 4：边界与降级

1. 无 binding：不渲染 Device 区域（或显示「未绑定设备」占位）
2. device 拉取失败：显示错误态，支持重试
3. vm_user 的 displayNum：可从 binding 或 device subjects 接口获取，若无则传 0（VmUserVNCView 可兼容）

---

## 6. 文件改动清单

| 文件 | 改动 |
|------|------|
| `novaic-app/src/hooks/useAgentBinding.ts` | 新建：封装 getBinding + devices.get |
| `novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | 数据源改为 useAgentBinding，按 subject 渲染 |
| `novaic-app/src/services/api.ts` | 确认 getAgentBinding 存在，必要时补充类型 |

---

## 7. 可选扩展

- **多 binding**：若未来支持一 agent 多 binding，则 `SubjectCardInfo[]` 可含多项，每项一张卡
- **displayNum**：若 Gateway 在 binding/subject 中返回 display_num，可传给 VmUserVNCView 用于展示

---

## 8. 风险与注意事项

1. **main 的 agent_id**：VNCViewShared 依赖 store 的 `currentAgentId`，需保证在选中该 agent 时 `currentAgentId` 正确
2. **vm_user 的 device_id**：必须使用 binding 的 `device_id`（非 agent_id），与 VmControl share 路径一致
3. **Android**：subject 一般为 `default`，device 需有 `device_serial` 供 Scrcpy 使用
