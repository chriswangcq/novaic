# VNC 连接不稳定问题修复检查清单

**依据**: `docs/VNC_INSTABILITY_DIAGNOSIS_REPORT.md`  
**执行方式**: 6 名 subagent 并行

---

## 一、Agent 1：P2P/Relay 修复

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 1.1 | **Relay session 过期时重新请求**：在 `connect_via_relay` 失败且错误含 "invalid" / "expired" / "session" 时，重新调用 `relay_request` 获取新 session_id 再重试 | `p2p/relay.rs`, `p2p/client.rs` | 重试时使用新 session |
| 1.2 | **relay_request 重试**：为 `relay_request` 添加 2-3 次重试，退避 500ms/1s | `p2p/rendezvous.rs` | 与 locate 类似的重试逻辑 |
| 1.3 | **PC 端 relay 重试**：cloud_bridge 收到 `connect_relay` 后，`connect_via_relay` 失败时重试 2-3 次 | `vmcontrol/cloud_bridge.rs` | 失败时自动重试 |

---

## 二、Agent 2：VncProxy 连接池修复

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 2.1 | **连接池健康检查/TTL**：复用前检查 `close_reason()`；可选：记录连接创建时间，超过 4-5 分钟则重建 | `vnc_proxy.rs` | 死连接不再被复用 |
| 2.2 | **移除坏连接时加锁**：`open_vnc_stream`/`open_scrcpy_stream` 失败时，在持有 `remote_conns` 锁的情况下移除 conn，避免竞态 | `vnc_proxy.rs` | 无并发复用坏连接 |
| 2.3 | **bind 失败时发送 port_tx**：`TcpListener::bind` 失败时，发送错误信号（如 `port_tx.send(Err(...))` 或约定 sentinel），setup 能区分 bind 失败 | `vnc_proxy.rs`, `setup.rs` | 真实失败原因可被记录 |

---

## 三、Agent 3：VncProxy 错误回传修复

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 3.1 | **send_ws_close 带 reason**：将 `Message::Close(None)` 改为 `Message::Close(Some(CloseFrame { code, reason }))`，传入具体错误信息 | `vnc_proxy.rs` | 前端能收到错误码和原因 |
| 3.2 | **route_vnc/route_scrcpy 错误传递**：确保 handler 中 `route_*` 返回的 Err 能转换为 Close reason 传给前端 | `vnc_proxy.rs` | 错误链路完整 |
| 3.3 | **WebSocket 升级超时**：对 `route_vnc`/`route_scrcpy` 的整个处理包一层 `tokio::time::timeout(30s)` | `vnc_proxy.rs` | 长时间卡住会超时关闭 |

---

## 四、Agent 4：前端错误处理修复

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 4.1 | **getVncUrl / get_scrcpy_proxy_url 加 .catch()**：`vmService.getVncUrl` 和 scrcpy 的 `getScrcpyProxyUrl` 调用处加 `.catch()`，失败时 `notifySubscribers(state, 'error', message)` | `vncStream.ts`, `scrcpyStream.ts` | 用户能看到具体错误 |
| 4.2 | **前端超时对齐**：VNC/scrcpy 的 WebSocket 连接超时从 15s 延长到 30-45s，或与后端 P2P+relay 耗时匹配 | `vncStream.ts`, `scrcpyStream.ts` | 减少「后端仍在连、前端已放弃」 |
| 4.3 | **wsUrl 缓存失效**：连接失败时清除 `state.wsUrl`，下次重试重新拉取 | `vncStream.ts` | 已有 testWebSocket 时清除，确认逻辑一致 |

---

## 五、Agent 5：Tunnel/VmControl 修复

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 5.1 | **find_vnc_target 重试**：`Path::exists()` 为 false 或 `UnixStream::connect` 失败时，短时重试（如 3 次，间隔 200ms） | `p2p/tunnel.rs` | VM 刚启动时能连上 |
| 5.2 | **Unix/TCP connect 超时**：`UnixStream::connect` 和 `TcpStream::connect` 包 `tokio::time::timeout(5-10s)` | `p2p/tunnel.rs`, `vmcontrol/vnc/mod.rs` | 不无限阻塞 |
| 5.3 | **VM 启动前清理 VNC socket**：在启动 QEMU 前，若存在旧的 VNC socket 文件则 `remove_file`，与 QMP 处理一致 | 查找 VM 启动逻辑（vmcontrol 或 gateway 侧） | 无残留 socket |
| 5.4 | **open_vnc_stream 超时**：`conn.open_bi()` 包 `tokio::time::timeout(15s)` | `p2p/tunnel.rs` 或调用处 | 避免长时间卡住 |

---

## 六、Agent 6：vnc_urls / 移动端修复

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 6.1 | **多 PC 设备选择**：`get_vnc_proxy_url` 若支持传入 `deviceId`（目标 PC 的 vmcontrol_device_id），则优先使用；否则保持「第一个在线」作为 fallback，并加注释说明 | `vnc_urls.rs` | 多 PC 时可指定目标 |
| 6.2 | **get_vnc_proxy_url 支持 deviceId 参数**：与 get_scrcpy_proxy_url 一致，接受可选 `deviceId`，前端在已知目标 PC 时传入 | `vnc_urls.rs`, `lib.rs` | API 一致 |
| 6.3 | **端口分配失败时更明确日志**：setup 中 port_rx 超时或收到错误时，记录更具体的日志（bind 失败 vs 超时） | `setup.rs` | 便于排查 |

---

## 七、执行顺序与依赖

- **Agent 1、2、3、5、6** 可并行（修改不同文件）
- **Agent 4** 依赖 3.1 的 Close reason 格式，可并行开发，但前端解析 reason 需与后端约定一致

---

## 八、验收检查

修复完成后，逐项确认：

- [ ] Relay 重试：断网后恢复，relay 能自动重连
- [ ] 连接池：休眠唤醒后，第一次 VNC 能连上（或快速失败并重试成功）
- [ ] 错误提示：VNC 失败时前端显示具体原因
- [ ] VM 启动：刚启动 VM 后点 VNC，能连上（或短时重试后连上）
- [ ] 多 PC：可选传入 deviceId 时能连到正确 PC

---

## 九、执行状态（2026-03-11）

| Agent | 状态 | 修改摘要 |
|-------|------|----------|
| 1 | ✅ 完成 | relay session 刷新、relay_request 重试、PC relay 重试 |
| 2 | ✅ 完成 | 连接池 TTL、坏连接同步移除、bind 失败通知 |
| 3 | ✅ 完成 | Close 带 reason、错误传递、30s 超时 |
| 4 | ✅ 完成 | invoke .catch、超时 30s、wsUrl 失效、解析 Close reason |
| 5 | ✅ 完成 | find_vnc_target 重试、connect 超时、VNC socket 清理、open_bi 超时 |
| 6 | ✅ 完成 | get_vnc_proxy_url deviceId、setup 日志 |

**构建**: `cargo check` 通过
