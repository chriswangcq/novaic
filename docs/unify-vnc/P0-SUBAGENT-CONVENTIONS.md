# P0 子任务约定（7 个 Subagent 必须遵守）

## 一、命名规范（全局约定）

| 语义 | 新命名 | 旧命名 | 适用层级 |
|------|--------|--------|----------|
| VNC 流标识 | `streamKey` | `agentId` | vncStream.ts |
| 资源标识 | `resourceId` | `agentId` | vm.ts、vncBridge.ts、vncTransport.ts、Tauri |
| 物理 PC 标识 | `pcClientId` | `deviceId` | 上述所有（VNC 路由上下文） |

## 二、invoke 与 Tauri 参数约定

- **前端 invoke**：`{ resourceId, pcClientId }`（camelCase，与 Tauri 命令参数名一致）
- **Tauri 命令**：`resourceId: String`、`pcClientId: Option<String>`（#[allow(non_snake_case)] 保持 camelCase）
- **内部变量**：Rust 用 `resource_id`、`device_id`（snake_case 为 pc_client_id 的局部变量名）

## 三、文件归属（禁止越界）

| Agent | 步骤 | 唯一修改文件 | 禁止修改 |
|-------|------|--------------|----------|
| 1 | P0-1+P0-6 | `novaic-app/src/services/vncStream.ts` | 其他 |
| 2 | P0-2 | `novaic-app/src/services/vncBridge.ts` | 其他 |
| 3 | P0-3 | `novaic-app/src/services/vm.ts` | 其他 |
| 4 | P0-4 | `novaic-app/src/services/vncTransport.ts` | 其他 |
| 5 | P0-5a | `novaic-app/src-tauri/src/commands/vnc_urls.rs` | 其他 |
| 6 | P0-5b | `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | 其他 |
| 7 | P0-7 | `novaic-app/src/components/Visual/VNCViewShared.tsx`、`novaic-app/src/components/Layout/DeviceFloatingPanel.tsx` | 其他 |

## 四、调用链约定（修改后必须一致）

```
vncStream.ts:  subscribeToVNCStream(streamKey, subscriber, pcClientId?)
               connectStream(streamKey, pcClientId?) 
               → vmService.getVncTransport(streamKey, pcClientId)

vm.ts:         getVncTransport(resourceId, pcClientId?)
               → VncBridgeTransport(resourceId, pcClientId) 或 getVncUrl(resourceId, pcClientId)

vncBridge.ts:  new VncBridgeTransport(resourceId, pcClientId)
               → invoke('vnc_bridge_connect', { resourceId, pcClientId })

vncTransport.ts: invoke('get_vnc_proxy_url', { resourceId, pcClientId })

Tauri:         get_vnc_proxy_url(resourceId, pcClientId)
               vnc_bridge_connect(resourceId, pcClientId)
```

## 五、P0-7 职责说明

Agent 7 负责**验证调用方**：
- VNCViewShared：已用 `streamKey`、`propPcClientId`，确认 `subscribeToVNCStream(streamKey, ..., propPcClientId)` 等调用与 vncStream 新 API 一致
- DeviceFloatingPanel：确认 `setVNCViewOnly(device.id, ...)` 等调用正确（device.id 即 streamKey）
- 若发现参数名或传参错误，进行修正；否则仅输出「验证通过」
