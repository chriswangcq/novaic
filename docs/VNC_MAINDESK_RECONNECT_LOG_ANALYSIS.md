# Maindesk 第一次连上、再连连不上 — 日志逐行分析

## 时间线

### 阶段 1：Maindesk 第一次连接（成功）

| 时间 | 事件 |
|------|------|
| 11:50:36.049864 | `vnc_stream_connect` resourceId=**666e2498...**（无 `:`，maindesk） |
| 11:50:36.049994 | 返回 stream_id=**b2bde72c** |
| 11:50:36.058165 | maindesk socket **找到** path=/tmp/novaic/novaic-vnc-666e2498....sock |
| 11:50:36.058268 | Unix socket **连接成功**，开始 proxy_quic_to_unix |

→ Maindesk 全链路成功，bridge 开始转发。

---

### 阶段 2：约 1.1 秒后 — Maindesk 被关闭

| 时间 | 事件 |
|------|------|
| 11:50:37.191118 | **vnc_stream_close** stream_id=**b2bde72c** |
| 11:50:37.191791 | vnc_stream_connect resourceId=**666e2498...:test**（有 `:test`，subuser） |
| 11:50:37.192194 | channel→quic 结束 rx 关闭 **send_count=12** |
| 11:50:37.192258 | bridge_channel_quic 结束，emit close |
| 11:50:37.192373 | route_vnc_to_channel 正常结束 stream_id=b2bde72c |

**根因**：用户从 maindesk 切到 subuser (test)。前端 `doConnect` 用新 transport 时关闭了 prevTransport，触发 `vnc_stream_close(b2bde72c)`。`send_count=12` 说明 maindesk 的 RFB 已发 12 个包，连接在正常使用中被关掉。

---

### 阶段 3：Subuser 切换（test → newtest → temp）

| 时间 | resourceId | send_count 结束时 |
|------|------------|------------------|
| 11:50:37 | :test | 837a23c6 被关时 send_count=**0**（切得太快，未握手） |
| 11:50:38 | :newtest | 80555667 被关时 send_count=**116**（已连接） |
| 11:50:39 | :temp | 33c889a4 被关时 send_count=**116**（已连接） |

---

### 阶段 4：切回 Maindesk（11:50:40）

| 时间 | 事件 |
|------|------|
| 11:50:40.494258 | vnc_stream_connect resourceId=**666e2498...**（无 `:`，maindesk） |
| 11:50:40.494468 | 返回 stream_id=**ed3339cd** |
| 11:50:40.495886 | maindesk 路径 查找 novaic-vnc-666e2498....sock |
| 11:50:40.495950 | maindesk socket **找到** |
| 11:50:40.496081 | Unix socket **连接成功**，开始 proxy_quic_to_unix |

→ 后端日志显示 maindesk 再次连接成功，socket 找到、Unix 连接建立。

---

## 结论

### 1. 后端层面

- Maindesk 第二次连接时：socket 找到、Unix 连接成功、proxy_quic_to_unix 已启动。
- 后端没有报错，也没有看到 `bridge_channel_quic 结束` 或 `vnc_stream_close` 针对 ed3339cd。

### 2. 问题在前端

后端对 maindesk 的第二次连接是成功的。若用户仍感觉「再连连不上」，更可能是：

1. **Transport 缓存**：maindesk 的 transport 在切到 subuser 时被 `close()`，已从 cache 移除。切回 maindesk 时 `createVncTransport` 会新建 transport，但若此时复用了旧的、已关闭的 transport 引用，就会出现异常。
2. **useVnc 的 prevTransport 逻辑**：切回 maindesk 时，若 `lastTransportRef` 还指向某个 subuser 的 transport，`doConnect` 会先关掉它再建新 RFB。若存在竞态或错误引用，可能误关或误用 transport。
3. **RFB 状态**：第二次 maindesk 连接时，RFB 可能未正确 `connect`，或很快被 disconnect，导致界面显示连不上。

### 3. 需要的前端日志

要确认「再连连不上」的具体原因，需要在前端补充日志，例如：

- `createVncTransport` 是否命中 cache、是否新建
- `useVnc` 的 `doConnect` 中 prevTransport / 当前 transport 的 streamId
- RFB 的 `connect` / `disconnect` 事件及触发时机

---

## 建议排查方向

1. **Transport cache**：maindesk 与 subuser 的 cache key 不同（`666e2498...|` vs `666e2498...:test|`），切回 maindesk 时应新建 transport，不会复用 subuser 的。需确认实际是否新建。
2. **快速切换**：subuser 间快速切换时，存在 `send_count=0` 即被关的情况（837a23c6），说明新 transport 到来时，旧 transport 被立刻关闭，可能导致 RFB 未完成握手。
3. **Maindesk 第二次**：后端显示连接成功，若前端仍异常，应重点查前端对 `vnc_stream:ed3339cd:data` 和 `vnc_stream:ed3339cd:close` 的监听与处理，以及 RFB 的创建与销毁时机。

---

## 4. DeviceDesktopView 的 deviceStatus 门控

`DeviceDesktopView` 对 maindesk 有额外条件：

```ts
if (isMaindesk && deviceStatus !== 'running') {
  setTransport(null);
  return;  // 不调用 createVncTransport
}
```

- 切回 maindesk 时，若组件重新挂载，`deviceStatus` 初始为 `'unknown'`
- 需等 `api.devices.status()` 返回 `'running'` 后才会创建 transport
- 若 API 慢或失败，maindesk 会一直不建 transport，表现为「再连连不上」
- 本次日志中 11:50:40 已有 `vnc_stream_connect`，说明当时 `deviceStatus` 已是 `'running'`，门控通过

---

## 5. 竞态：同一 resourceId 的多次 connect

日志中 11:50:37 出现**同一 resourceId 的两次 connect 几乎同时**：

```
11:50:37.191791  vnc_stream_connect resourceId=666e2498...:test  → stream c9034155
11:50:37.192032  vnc_stream_connect resourceId=666e2498...:test  → stream 77af72be
```

说明前端在极短时间内对同一 subuser 发起了两次 `createVncTransport`，可能来自：

- effect 重复执行（依赖变化）
- 或父组件渲染导致子组件多次挂载

这会导致：先建的 stream 很快被后建的 stream 对应的 transport 的 `prevTransport.close()` 关掉，出现 `send_count=0` 即断开的 subuser 连接。
