# P2P Phase 4 代码 Review 报告

> 6 名 subagent 对照 DESIGN-P2P-UNIFIED.md 对 novaic-app 未提交改动进行挑刺式 review。
> 生成时间：2026-03-11

---

## 一、问题汇总（按严重程度）

### 高优先级

| # | 问题 | 来源 | 修复建议 |
|---|------|------|----------|
| 1 | **CloudBridge 使用建连时 token 快照，长连接下 JWT 可能过期** | Agent 2 | ConnectRelay 处理时从 `cloud_token.read().await` 重新读取，而非使用 connect_and_run 入参 |
| 2 | **relay 竞态：手机先连 relay 会失败** | Agent 4 | relay 要求 PC 先 RegisterPc，手机后 ConnectRequest。手机在 HTTP 响应中立即拿到 session_id，PC 通过 WS 推送有延迟。建议：手机 connect_via_relay 失败时重试（2s/4s/8s 指数退避） |
| 3 | **IPv6 relay_url 解析错误** | Agent 3 | `https://[::1]:443/p2p/relay` 时 `format!("{}:{}", "::1", 443)` → `"::1:443"` 无法 parse。需对 IPv6 host 使用 `[host]:port` 格式 |
| 4 | **tunnel stream resource_id 超 255 字节导致 u8 溢出** | Agent 6 | `write_stream_header` 中 `id_len = resource_id.as_bytes().len() as u8` 会溢出。需校验 `resource_id.len() <= 255` 并返回错误 |

### 中优先级

| # | 问题 | 来源 | 修复建议 |
|---|------|------|----------|
| 5 | CloudBridge 直接 import p2p::relay，违反分层 | Agent 2 | 改用 `P2pClient::connect_via_relay`；run_tunnel_server 通过 p2p 顶层暴露 |
| 6 | spawn 内错误不传播，手机侧无失败反馈 | Agent 2 | 向 Gateway 发送 relay_connect_failed 消息 |
| 7 | P2pClientConfig.discovery 为 Option，与设计「Discovery 注入」不符 | Agent 1 | 文档明确 discovery 可选场景；或 DirectOnly 时强制要求 discovery |
| 8 | DirectThenRelay 分支 fall-through 可读性差 | Agent 1 | 显式 `return relay::punch_or_relay(...)` 或加注释 |
| 9 | relay 超时 30s/15s 可能不足，无重试 | Agent 3 | 可配置超时；失败时重试 2 次 |
| 10 | relay ok:false 无结构化错误类型 | Agent 3 | 定义 RelayError 枚举，基于 error 文本映射 |
| 11 | STUN 未抽离到独立 stun.rs | Agent 5 | 新建 stun.rs，从 rendezvous 迁出 get_external_addr 等 |
| 12 | P2P 未启动时本地 VNC 提示不明确 | Agent 4 | p2p_setup_error 存在时直接返回更清晰错误 |
| 13 | session 重复导致 PC 多余连接 | Agent 6 | 移动端短时去重 relay_request；或 Gateway 幂等 |
| 14 | NOVAIC_RELAY_INSECURE 文档缺失 | Agent 6 | README 明确仅限开发，严禁生产 |
| 15 | relay 过期 session 被动清理 | Agent 6 | relay 增加定时 cleanup 任务 |

### 低优先级

| # | 问题 | 来源 | 修复建议 |
|---|------|------|----------|
| 16 | connect 签名多 gateway_url/token，设计文档未体现 | Agent 1 | 更新 DESIGN-P2P-UNIFIED.md |
| 17 | relay_client_tls 每次新建 | Agent 3 | OnceLock 缓存 |
| 18 | hole_punch 未重命名为 transport.rs | Agent 5 | 技术债，可后续排期 |
| 19 | device_id 无格式/长度校验 | Agent 6 | 限制 max 128 字节 |

---

## 二、各 Agent 结论摘要

### Agent 1：P2pClient / ConnectStrategy
- connect 多参数合理（relay 回退需 gateway_url/token）
- DirectThenRelay 逻辑正确，但 fall-through 易误解
- connect_via_descriptor 对 Relay bail 合理

### Agent 2：CloudBridge
- **高**：token 用建连时快照，长连接会过期
- **中**：违反分层（直接 p2p::relay）；错误不传播

### Agent 3：relay.rs
- 协议字段与 novaic-quic-service 一致
- **高**：IPv6 解析错误
- **中**：超时、结构化错误、TLS 缓存

### Agent 4：VncProxy
- remote_conns 与 CloudBridge 分离设计正确
- **高**：PC/手机谁先连 relay 的竞态
- **中**：P2P 未启动时本地 VNC 提示

### Agent 5：目录结构
- CompositeRegistry/Discovery 已实现
- NOVAIC_STUN_SERVER 已支持
- **中**：stun 未抽离；**低**：hole_punch 未重命名

### Agent 6：安全/边界
- **高**：resource_id u8 溢出
- **中**：session 重复、超时体验、NOVAIC_RELAY_INSECURE、relay cleanup
- JWT 在 QUIC TLS 下安全

---

## 三、建议修复顺序

1. **立即**：CloudBridge token 重新读取（高）
2. **立即**：relay IPv6 解析（高）
3. **立即**：tunnel resource_id 255 校验（高）
4. **短期**：手机 connect_via_relay 重试（高）
5. **短期**：CloudBridge 改用 P2pClient::connect_via_relay（中）
6. **中期**：relay 结构化错误、超时配置、定时 cleanup
7. **可选**：stun 抽离、transport 重命名、文档更新
