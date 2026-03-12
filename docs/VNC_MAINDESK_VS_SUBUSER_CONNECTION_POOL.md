# Maindesk vs Subuser 连接池差异分析

三轮思考记录。

---

## 第一轮：连接池对 maindesk 和 subuser 是否一视同仁？

### 结论：**连接池逻辑完全相同**

| 维度 | maindesk | subuser | 说明 |
|------|----------|---------|------|
| **resource_id** | `{device_id}` | `{device_id}:{username}` | 不同 key，互不驱逐 |
| **连接池规则** | 同一 resource_id 仅 1 个 stream | 同上 | 完全一致 |
| **新连接驱逐旧连接** | ✓ | ✓ | 同一 resource_id 时 |
| **30s 空闲超时** | ✓ | ✓ | 完全一致 |
| **touch 保活** | quic 收数据 + 20s 心跳 | 同上 | 完全一致 |

**关键点**：maindesk 和 subuser 的 resource_id 不同，因此：
- 连 maindesk 不会驱逐 subuser
- 连 subuser 不会驱逐 maindesk
- 同一设备下，maindesk 与多个 subuser 可同时存在

---

## 第二轮：前端 / 后端对 maindesk 和 subuser 的差异

### 前端差异

| 维度 | maindesk | subuser |
|------|----------|---------|
| **deviceStatus 门控** | 必须 `deviceStatus === 'running'` 才建连 | 无门控，直接建连 |
| **deviceStatus 来源** | 拉取 `api.devices.status` | 不拉取，始终 `unknown` |
| **初始 deviceStatus** | 可用 `device?.status` 做乐观初始值 | 无 |
| **createVncTransport 超时** | 30s（可配置） | 60s（subuser 需轮询 port 文件） |

### 后端差异（vnc_endpoint / tunnel）

| 维度 | maindesk | subuser |
|------|----------|---------|
| **VNC socket 路径** | `novaic-vnc-{device_id}.sock` | `vnc-{device_id}-{username}.sock` |
| **发现方式** | 直接查 socket 文件 | 轮询 port 文件 `vnc-{username}.port` |
| **连接池 key** | `resource_id = device_id` | `resource_id = device_id:username` |

### 连接池本身

连接池只按 `resource_id` 管理，不区分 maindesk/subuser，逻辑统一。

---

## 第三轮：日志中的「Disconnection timed out」与切换行为

### 日志时序摘要

1. **maindesk** 连接成功 → 切到 **subuser :newtest** → Bridge.close(maindesk)
2. **subuser :newtest** 连接成功 → 切到 **subuser :test** → Bridge.close(:newtest)
3. **subuser :test** 连接成功，RFB connect 成功，收到 data #1..#100
4. 随后出现 `[Error] Disconnection timed out`

### 「Disconnection timed out」来源

来自 noVNC：调用 `rfb.disconnect()` 后，若底层 transport 在 3 秒内未完成关闭，会打印该错误。

### 可能原因

1. **Bridge.close() 不调用后端**：前端只做本地 cleanup，不调用 `vnc_stream_close`，后端 stream 仍存在
2. **noVNC 等待「真正关闭」**：noVNC 可能期望 transport 像 WebSocket 一样完成关闭握手，而我们的 Bridge 只是设 `readyState=CLOSED`，没有实际关闭流程
3. **快速切换**：从 :newtest 切到 :test 时，先 close(:newtest)，再 doConnect(:test)，close 触发 disconnect，disconnect 可能卡在等待 transport 关闭

### 连接池与切换

- 从 maindesk 切到 subuser：maindesk 与 subuser 的 resource_id 不同，连接池不会互相驱逐
- 从 subuser :newtest 切到 subuser :test：resource_id 不同，也不会互相驱逐
- 前端 Bridge.close() 只做本地清理，后端 stream 会由 30s 空闲超时或新连接驱逐来回收

---

## 总结表

| 层级 | maindesk | subuser | 连接池是否区分 |
|------|----------|---------|----------------|
| **连接池 key** | device_id | device_id:username | 否，仅 key 不同 |
| **连接池规则** | 1 stream/resource_id, 30s 空闲 | 同上 | 否 |
| **前端门控** | deviceStatus=running | 无 | 是 |
| **后端发现** | 直接 socket | port 轮询 | 是 |
| **超时** | 30s | 60s | 是 |

**核心结论**：连接池对 maindesk 和 subuser 使用同一套逻辑，差异只体现在 resource_id 和前后端的业务处理上。
