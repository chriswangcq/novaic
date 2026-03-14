# Maindesk 切回失败 — 连接池逻辑分析

## 场景

1. maindesk 刚启动 → 连接成功，有画面 ✓
2. 切到 subuser → 正常 ✓
3. 切回 maindesk → 失败 ✗

## 连接池逻辑回顾

| 规则 | 实现 |
|------|------|
| 按 resource_id 唯一 | `by_resource: HashMap<resource_id, (stream_id, last_activity)>` |
| 新连接踢旧连接 | `evict_for_resource()` 在 `vnc_stream_connect` 时先驱逐同 resource_id 的旧 stream |
| 30s 空闲关闭 | 后台任务每 5s 检查，超时则 drop tx、emit close |
| 前端不主动关闭 | `vncBridge.close()` 不再调用 `vnc_stream_close` |

## 切 maindesk → subuser 时

1. 前端 `doConnect` 用 subuser transport，会 `prevTransport.close()` 关掉 maindesk transport
2. `close()` 只做：unlisten、evictFromCache，**不**调用 `vnc_stream_close`
3. 后端 maindesk stream 仍在：`by_resource[666e2498...]`、`streams[stream_id_A]` 都还在
4. 前端不再 send，但 quic 仍会收到 VNC 帧 → `touch()` 仍会更新 `last_activity` → 不会 30s 超时

## 切 subuser → maindesk 时

1. 前端切回 maindesk，`createVncTransport` 被调用
2. maindesk 的 transport 之前被 evictFromCache，cache 为空，会新建 transport
3. 新建 transport 会 `connect()` → `vnc_stream_connect(666e2498...)`
4. 后端 `evict_for_resource(666e2498...)`：
   - 找到旧 stream_id_A，drop tx_A
   - 旧 route 任务因 rx 关闭而退出
   - emit close 给 stream_id_A（前端已 unlisten，不会收到）
5. 新建 stream_id_B，插入 `streams`、`by_resource`
6. spawn 新的 `route_vnc_to_channel`，建立新连接

从连接池逻辑看，切回 maindesk 时后端会正确驱逐旧连接并建立新连接。

---

## 可能原因

### 1. DeviceDesktopView 的 deviceStatus 门控（最可疑）

```ts
if (isMaindesk && deviceStatus !== 'running') {
  setTransport(null);
  return;  // 不调用 createVncTransport
}
```

- 切回 maindesk 时组件重新挂载，`deviceStatus` 初始为 `'unknown'`
- 必须等 `api.devices.status()` 返回 `'running'` 才会创建 transport
- 若 API 返回 `'stopped'`、`'unknown'` 或失败，**永远不会** `createVncTransport`
- 表现：一直停在「VM is stopped」或「Waiting for VM」，没有 VNC 画面

**排查**：切回 maindesk 时看控制台是否有 `createVncTransport` 日志；若没有，多半是 `deviceStatus !== 'running'`。

### 2. 30s 空闲在切 subuser 期间触发

- 切到 subuser 后，maindesk 的 stream 不再有前端 send
- 若 VNC 端也长时间不发帧（例如黑屏、无变化），`touch()` 可能很久不被调用
- 若超过 30s 无活动，空闲任务会关闭 maindesk stream
- 切回 maindesk 时，`evict_for_resource` 找不到旧 stream，会直接新建
- 理论上仍应能新建连接，除非新建流程本身失败

### 3. createVncTransport 的 cache 误用

- maindesk key：`666e2498...|`
- subuser key：`666e2498...:test|`
- 两者不同，不会误用
- 切回 maindesk 时 cache 已被 evict，会新建 transport，逻辑正常

### 4. useVnc 的 transport=null 导致 disconnect

- 切回 maindesk 时，若 `createVncTransport` 尚未 resolve，`transport` 可能短暂为 null
- effect 会执行 `disconnect()`，关闭 `lastTransportRef`（即 subuser transport）
- subuser transport 被 close，但不会调用 `vnc_stream_close`，后端 subuser stream 仍在
- 对 maindesk 无直接影响，但可能影响 subuser 的后续使用

### 5. 后端 evict 与新建的竞态

- `evict_for_resource` 与新建 stream 是顺序执行，无并发
- 新建在 evict 之后，逻辑上不会有竞态问题

---

## 建议排查步骤

1. **确认是否走到 createVncTransport**
   - 切回 maindesk 时，看是否有 `[VNC-FLOW] [1-前端] createVncTransport 开始 resourceId=666e2498...`
   - 若没有 → 优先怀疑 `deviceStatus !== 'running'` 门控

2. **确认 deviceStatus**
   - 在 `DeviceDesktopView` 的 effect 中加日志，打印 `deviceStatus`
   - 若长期为 `'unknown'` 或 `'stopped'` → 检查 `api.devices.status()` 的返回和 Gateway 的 `_is_linux_device_running`

3. **确认后端是否新建 stream**
   - 切回 maindesk 时，看是否有 `vnc_stream_connect 开始 resourceId=666e2498...` 和 `连接池 驱逐旧连接`
   - 若有驱逐但无新建成功 → 排查 `route_vnc_to_channel` 或 `ensure_vnc_endpoint`

4. **确认 RFB 是否连上**
   - 看是否有 `[VNC-FLOW] [3-useVnc] RFB connect 成功`
   - 若没有 → 可能是 transport 已 closed 或 RFB 握手失败

---

## 若确认是 deviceStatus 门控

可考虑：

1. **放宽门控**：maindesk 在 `deviceStatus === 'unknown'` 时也尝试创建 transport，由后端决定是否可用
2. **复用已有状态**：切回 maindesk 时，若全局 store 中该设备已是 `running`，可直接用，不等 API 再查一次
3. **优化 API**：保证 Gateway 的 `_is_linux_device_running` 在 VM 实际运行时稳定返回 `running`
