# P0 → P1 → P2 实施指南：Agent 与 Device 分离

> 基于 4 名 subagent 调研结果整理。调研报告：
> - `docs/VNCSTREAM_AGENTID_TO_STREAMKEY_CALL_CHAIN.md`
> - `docs/DEVICE_MANAGER_FLOATING_PANEL_DATA_SOURCE_RESEARCH.md`
> - Tauri 命令调研（get_vnc_proxy_url、vnc_bridge_connect）
> - vm.ts getVncUrl/getVncTransport 调用链调研

---

## 调研结论摘要

| 调研项 | 结论 |
|--------|------|
| **vncStream** | 13 个导出函数第一参数均为 agentId，实际语义为 streamKey；调用方仅 VNCViewShared、DeviceFloatingPanel；VNCViewShared 已用 streamKey 变量 |
| **Tauri 命令** | get_vnc_proxy_url、vnc_bridge_connect 的 agentId 实际为 resourceId；deviceId 实际为 pcClientId；vncTransport.ts 已用 resourceId/pcClientId 传参 |
| **vm.ts** | getVncUrl/getVncTransport 仅被 vncStream.connectStream 调用；参数来源 streamKey + propPcClientId |
| **DeviceManagerPage** | 设备详情：selectedDeviceId === agentDevice.id 时用 agentDevice，否则 devices.find；可改为 devices.get 为主 |
| **DeviceFloatingPanel** | 完全依赖 useAgentBinding；无 Agent 不渲染；需支持 deviceMode |

---

## P0：VNC 层去 agentId 化

### P0-1：vncStream.ts 重命名 agentId → streamKey

**文件**：`novaic-app/src/services/vncStream.ts`

**修改清单**：

1. 注释 `// 全局流状态存储，按 agentId 管理` → `// 全局流状态存储，按 streamKey 管理`
2. `connectStream(agentId, deviceId)` → `connectStream(streamKey, pcClientId?)`
3. `disconnectStream(agentId)` → `disconnectStream(streamKey)`
4. 内部 `streams.get(agentId)` / `streams.set(agentId, ...)` → `streamKey`
5. `state.deviceId` 保留（语义为 pc_client_id，用于重连）
6. 所有导出函数第一参数 `agentId` → `streamKey`，第二参数 `deviceId` → `pcClientId`（仅 subscribeToVNCStream、reconnectVNCStream 有第二参数）
7. JSDoc 更新 `@param agentId` → `@param streamKey`

**补丁**：见下方「P0 补丁」小节。

---

### P0-2：vncBridge.ts 重命名 agentId → resourceId

**文件**：`novaic-app/src/services/vncBridge.ts`

**修改**：

```diff
- constructor(
-   private agentId: string,
-   private deviceId?: string
  ) {}
+ constructor(
+   private resourceId: string,
+   private pcClientId?: string
+ ) {}
```

```diff
- this.bridgeId = await invoke<string>('vnc_bridge_connect', {
-   agentId: this.agentId,
-   deviceId: this.deviceId ?? null,
+ this.bridgeId = await invoke<string>('vnc_bridge_connect', {
+   resourceId: this.resourceId,
+   pcClientId: this.pcClientId ?? null,
+ });
```

---

### P0-3：vm.ts getVncUrl / getVncTransport 参数重命名

**文件**：`novaic-app/src/services/vm.ts`

**修改**：

```diff
  /**
   * 获取 VNC WebSocket URL（统一代理，OS 动态端口）。
   *
   * @param agentId - VM/agent 标识
   * @param deviceId - 可选：vmcontrol_device_id（目标 PC），多 PC 时传入可指定目标；未传则从 my-devices 取第一个在线
   */
- async getVncUrl(agentId: string, deviceId?: string): Promise<string> {
-   const url = await invoke<string>('get_vnc_proxy_url', { agentId, deviceId });
+ async getVncUrl(resourceId: string, pcClientId?: string): Promise<string> {
+   const url = await invoke<string>('get_vnc_proxy_url', { resourceId, pcClientId });
    return url;
  }
```

```diff
  async getVncTransport(
-   agentId: string,
-   deviceId?: string
+   resourceId: string,
+   pcClientId?: string
  ): Promise<string | VncBridgeTransport> {
    if (shouldUseVncBridge()) {
-     const transport = new VncBridgeTransport(agentId, deviceId);
+     const transport = new VncBridgeTransport(resourceId, pcClientId);
      await transport.connect();
      return transport;
    }
-   return this.getVncUrl(agentId, deviceId);
+   return this.getVncUrl(resourceId, pcClientId);
  }
```

---

### P0-4：vncTransport.ts invoke 参数名

**文件**：`novaic-app/src/services/vncTransport.ts`

**修改**：

```diff
    const url = await invoke<string>('get_vnc_proxy_url', {
-     agentId: resourceId,
-     deviceId: pcClientId ?? null,
+     resourceId,
+     pcClientId: pcClientId ?? null,
    });
```

---

### P0-5：Tauri 命令参数重命名

**文件**：`novaic-app/src-tauri/src/commands/vnc_urls.rs`

**修改**：

```diff
 #[tauri::command]
 pub async fn get_vnc_proxy_url(
     ...
     #[allow(non_snake_case)]
-    agentId: String, // VM/agent 标识
+    resourceId: String, // VM 资源：maindesk 为 device_id，subuser 为 device_id:username
     #[allow(non_snake_case)]
-    deviceId: Option<String>, // 可选：vmcontrol_device_id（目标 PC）
+    pcClientId: Option<String>, // 可选：物理 PC 标识（目标 PC）
 ) -> Result<String, String> {
-    let agent_id = agentId;
+    let resource_id = resourceId;
     ...
-    let device_id = p.local_vmcontrol... .or(deviceId);
+    let device_id = p.local_vmcontrol... .or(pcClientId);
     ...
-    Ok(p.ws_url(&device_id, &agent_id))
+    Ok(p.ws_url(&device_id, &resource_id))
 }
```

**文件**：`novaic-app/src-tauri/src/commands/vnc_bridge.rs`

**修改**：

```diff
 #[tauri::command]
 pub async fn vnc_bridge_connect(
     ...
     #[allow(non_snake_case)]
-    agentId: String,
+    resourceId: String,
     #[allow(non_snake_case)]
-    deviceId: Option<String>,
+    pcClientId: Option<String>,
 ) -> Result<String, String> {
-    let device_id = resolve_device_id(..., deviceId).await?;
-    let agent_id = agentId;
+    let device_id = resolve_device_id(..., pcClientId).await?;
+    let resource_id = resourceId;
     ...
-    p.ws_url(&device_id, &agent_id)
+    p.ws_url(&device_id, &resource_id)
 }
```

**注意**：`resolve_device_id` 参数需同步改为 `pcClientId`。

---

### P0-6：vncStream 内部调用 vmService 更新

**文件**：`novaic-app/src/services/vncStream.ts`

**修改**：

```diff
- state.transportOrUrl = await vmService.getVncTransport(agentId, deviceId).catch(...);
+ state.transportOrUrl = await vmService.getVncTransport(streamKey, pcClientId).catch(...);
```

```diff
- connectStream(agentId, pcId);
+ connectStream(streamKey, pcId);
```

（connectStream 内部 state.deviceId 存储 pcClientId，重连时使用）

---

### P0-7：VNCViewShared 与 DeviceFloatingPanel
VNCViewShared 已使用 `streamKey` 变量，调用 `subscribeToVNCStream(streamKey, ..., propPcClientId)`，参数名变更后无需改调用方式。DeviceFloatingPanel 传入 `device.id`，语义正确，只需适配 vncStream 新参数名。

---

## P0 补丁汇总（可直接应用）

### vncStream.ts

```diff
--- a/novaic-app/src/services/vncStream.ts
+++ b/novaic-app/src/services/vncStream.ts
@@ -42,7 +42,7 @@ interface StreamState {
   connectRequestId: number;
 }
 
-// 全局流状态存储，按 agentId 管理
+// 全局流状态存储，按 streamKey 管理
 const streams = new Map<string, StreamState>();
 
 // ==================== 内部函数 ====================
@@ -123,13 +123,13 @@ function stopFrameCapture(state: StreamState) {
   }
 }
 
-async function connectStream(agentId: string, deviceId?: string) {
-  let state = streams.get(agentId);
+async function connectStream(streamKey: string, pcClientId?: string) {
+  let state = streams.get(streamKey);
   if (!state) {
     state = createStreamState();
-    streams.set(agentId, state);
+    streams.set(streamKey, state);
   }
-  state.deviceId = deviceId;
+  state.deviceId = pcClientId;
   const reqId = ++state.connectRequestId;
 
   // 如果已经连接或正在连接，不重复连接
@@ -143,7 +143,7 @@ async function connectStream(agentId: string, deviceId?: string) {
     // 获取传输（OTA 模式为 VncBridgeTransport，否则为 WebSocket URL）
     if (!state.transportOrUrl) {
-      state.transportOrUrl = await vmService.getVncTransport(agentId, deviceId).catch((err: any) => {
+      state.transportOrUrl = await vmService.getVncTransport(streamKey, pcClientId).catch((err: any) => {
         ...
       });
     }
@@ -185,7 +185,7 @@ async function connectStream(agentId: string, deviceId?: string) {
     // 后续日志中的 agentId 改为 streamKey
-    console.log(`[VNCStream] Connected to ${agentId}`);
+    console.log(`[VNCStream] Connected to ${streamKey}`);
     ...
-    console.log(`[VNCStream] Disconnected from ${agentId}:`, clean ? 'clean' : 'unclean', reason || '');
+    console.log(`[VNCStream] Disconnected from ${streamKey}:`, clean ? 'clean' : 'unclean', reason || '');
     ...
-    console.log(`[VNCStream] Scheduling reconnect for ${agentId} (${state.retryCount}/${VNC_MAX_RETRIES}) in ${delay}ms`);
+    console.log(`[VNCStream] Scheduling reconnect for ${streamKey} (${state.retryCount}/${VNC_MAX_RETRIES}) in ${delay}ms`);
     ...
-    connectStream(agentId, pcId);
+    connectStream(streamKey, pcId);
     ...
-    console.error(`[VNCStream] Security failure for ${agentId}:`, e.detail?.reason);
+    console.error(`[VNCStream] Security failure for ${streamKey}:`, e.detail?.reason);
     ...
-    console.error(`[VNCStream] Failed to connect to ${agentId}:`, e);
+    console.error(`[VNCStream] Failed to connect to ${streamKey}:`, e);
     ...
-    connectStream(agentId, pcId);
+    connectStream(streamKey, pcId);
 }
 
-function disconnectStream(agentId: string) {
-  const state = streams.get(agentId);
+function disconnectStream(streamKey: string) {
+  const state = streams.get(streamKey);
   ...
-  streams.delete(agentId);
+  streams.delete(streamKey);
 }
 
 /**
- * @param agentId Agent ID
+ * @param streamKey VNC 流标识（maindesk: device_id；subuser: device_id:username）
  * @param deviceId - 可选：pc_client_id，多 PC 时指定目标
  */
-export function subscribeToVNCStream(agentId: string, subscriber: StreamSubscriber, deviceId?: string): () => void {
+export function subscribeToVNCStream(streamKey: string, subscriber: StreamSubscriber, pcClientId?: string): () => void {
   ...
-  connectStream(agentId, deviceId);
+  connectStream(streamKey, pcClientId);
   ...
-  disconnectStream(agentId);
+  disconnectStream(streamKey);
 }
 
-export function getVNCStreamCanvas(agentId: string): HTMLCanvasElement | null {
-  const state = streams.get(agentId);
+export function getVNCStreamCanvas(streamKey: string): HTMLCanvasElement | null {
+  const state = streams.get(streamKey);
   ...
 }
 
-export function getVNCStreamStatus(agentId: string): StreamStatus {
-  const state = streams.get(agentId);
+export function getVNCStreamStatus(streamKey: string): StreamStatus {
+  const state = streams.get(streamKey);
   ...
 }
 
-export function setVNCViewOnly(agentId: string, viewOnly: boolean) {
-  const state = streams.get(agentId);
+export function setVNCViewOnly(streamKey: string, viewOnly: boolean) {
+  const state = streams.get(streamKey);
   ...
 }
 
-export function sendVNCKey(agentId: string, ...) {
+export function sendVNCKey(streamKey: string, ...) {
   ...
 }
 
-export function reconnectVNCStream(agentId: string, deviceId?: string) {
+export function reconnectVNCStream(streamKey: string, pcClientId?: string) {
   ...
-  disconnectStream(agentId);
-  setTimeout(() => connectStream(agentId, state.deviceId), 100);
+  disconnectStream(streamKey);
+  setTimeout(() => connectStream(streamKey, state.deviceId), 100);
 }
 
-export function getVNCRFB(agentId: string): RFB | null {
+export function getVNCRFB(streamKey: string): RFB | null {
   ...
 }
 
-export function attachVNCContainer(agentId: string, parent: HTMLElement): boolean {
+export function attachVNCContainer(streamKey: string, parent: HTMLElement): boolean {
   ...
 }
 
-export function detachVNCContainer(agentId: string): void {
+export function detachVNCContainer(streamKey: string): void {
   ...
 }
```

---

## P1：Device 管理去 Agent 优先

### P1-1：DeviceManagerPage 数据源改为 devices.get 为主

**目标**：设备详情统一用 `devices.get(selectedDeviceId)`，不再依赖 `agentDevice` 作为主数据源。

**文件**：`novaic-app/src/components/VM/DeviceManagerPage.tsx`

**修改**：

1. 新增 `useDevice(deviceId)` 或直接用 `api.devices.get(selectedDeviceId)` 获取选中设备详情
2. 移除「选中设备 = Agent 绑定设备时优先用 agentDevice」的逻辑
3. 保留 `useAgentDevice` 仅用于 `isAgentDevice` 高亮（可选：在选中设备行旁显示「当前 Agent 绑定」）

**实现**：

```typescript
// 原逻辑
useEffect(() => {
  if (!selectedDeviceId) {
    setSelectedDevice(null);
    return;
  }
  const fromAgent = agentDevice?.id === selectedDeviceId ? agentDevice : null;
  const next = fromAgent ?? devices.find(d => d.id === selectedDeviceId) ?? null;
  setSelectedDevice(next);
}, [devices, selectedDeviceId, agentDevice]);

// 改为：以 devices 为主，必要时用 devices.get 刷新
useEffect(() => {
  if (!selectedDeviceId) {
    setSelectedDevice(null);
    return;
  }
  const fromList = devices.find(d => d.id === selectedDeviceId);
  if (fromList) {
    setSelectedDevice(fromList);
    return;
  }
  // 列表未包含（如刚添加、刷新滞后）时，用 devices.get
  api.devices.get(selectedDeviceId).then(d => {
    if (selectedDeviceId === useAppStore.getState().selectedDeviceId) {
      setSelectedDevice(d);
    }
  }).catch(() => setSelectedDevice(null));
}, [devices, selectedDeviceId]);
```

**可选**：保留 `useAgentDevice` 仅用于 `isAgentDevice = agentDevice?.id === selectedDeviceId`，用于 UI 高亮。

---

### P1-2：DeviceFloatingPanel 支持 deviceMode（可选）✅ 已完成

**目标**：当传入 `deviceId`、`subjectType`、`subjectId?` 时，不依赖 Agent，直接使用 devices.get 获取设备信息。

**实现**：

1. 新增 props：`deviceMode?: DeviceModeConfig`（`{ deviceId, subjectType, subjectId? }`）
2. 当 `deviceMode` 存在时：使用 `useDeviceVncTarget` 获取 device，构造 synthetic binding 与 `SubjectCardInfo`
3. 当 `deviceMode` 不存在时：保持原有 `useAgentBinding` 逻辑
4. VNCViewShared 新增 `onStart` prop，deviceMode 时用 `api.devices.start` 替代 `vmService.start`

---

## P2：新增 useDeviceVncTarget

### P2-1：新增 useDeviceVncTarget

**文件**：`novaic-app/src/hooks/useDeviceVncTarget.ts`（新建）

```typescript
/**
 * useDeviceVncTarget — 纯 Device 体系的 VncTarget 获取
 *
 * 不依赖 Agent，直接通过 deviceId + subjectType + subjectId 构造 VncTarget。
 * 用于 DeviceManagerPage、DeviceFloatingPanel 的 deviceMode。
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { Device } from '../types';
import type { VncTarget } from '../types/vnc';

export interface UseDeviceVncTargetResult {
  device: Device | null;
  vncTarget: VncTarget | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useDeviceVncTarget(
  deviceId: string | null,
  subjectType: 'main' | 'vm_user' | 'default',
  subjectId?: string | null
): UseDeviceVncTargetResult {
  const [device, setDevice] = useState<Device | null>(null);
  const [vncTarget, setVncTarget] = useState<VncTarget | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!deviceId) {
      setDevice(null);
      setVncTarget(null);
      setIsLoading(false);
      setError(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const d = await api.devices.get(deviceId);
      setDevice(d);
      const resourceId =
        subjectType === 'vm_user' && subjectId
          ? `${deviceId}:${subjectId}`
          : deviceId;
      setVncTarget({
        resourceId,
        subjectType,
        deviceId,
        username: subjectType === 'vm_user' ? subjectId : undefined,
        pcClientId: d.pc_client_id,
      });
    } catch (e: any) {
      setError(e?.message || 'Failed to load device');
      setDevice(null);
      setVncTarget(null);
    } finally {
      setIsLoading(false);
    }
  }, [deviceId, subjectType, subjectId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { device, vncTarget, isLoading, error, refetch: fetch };
}
```

---

## 实施顺序建议

| 阶段 | 步骤 | 依赖 | 风险 |
|------|------|------|------|
| **P0** | P0-1 vncStream | 无 | 低 |
| **P0** | P0-2 vncBridge | 无 | 低 |
| **P0** | P0-3 vm.ts | 无 | 低 |
| **P0** | P0-4 vncTransport | 无 | 低 |
| **P0** | P0-5 Tauri 命令 | 无 | 中（需前后端同步） |
| **P0** | P0-6 vncStream 内部 | P0-1, P0-3 | 低 |
| **P1** | P1-1 DeviceManagerPage | 无 | 中 |
| **P1** | P1-2 DeviceFloatingPanel deviceMode | 可选 | 低 |
| **P2** | P2-1 useDeviceVncTarget | 无 | 低 |

**建议**：P0 一次性完成（前后端同步发布），P1、P2 可分批进行。

---

## 附录：Tauri 权限文件

若 `permissions/allow-app-commands.toml` 或 `capabilities` 中显式列出 `get_vnc_proxy_url`、`vnc_bridge_connect` 的参数，需同步更新参数名。当前 Tauri 2 的 invoke 通常不校验参数名，仅需前后端参数名一致即可。
