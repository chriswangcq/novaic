# Phase 1+2+3+4 整体测试审查报告

> 4 名测试工程师对 Phase 1–4 整体变更的挑刺式审查。接受客观意见并修复。

---

## 一、测试工程师 1：数据流与一致性

### 1.1 P2pClient connect 流程（Phase 4 已修复）

- DirectOnly / DirectThenRelay / RelayOnly 分支正确 ✓
- discovery=None 时 DirectThenRelay 走 punch_or_relay，需 gateway_url ✓（caller 传入）

### 1.2 get_vnc_proxy_url / get_scrcpy_proxy_url 移动端

- 移动端 local_vmcontrol=None 时，从 my-devices 取第一个 online device_id ✓
- get_scrcpy_proxy_url deviceId=None 时同逻辑 ✓（Phase 1-2-3 已修复）

### 1.3 发现

- **p2p lib.rs 模块列表**：未列出 `relay`（Phase 4 新增），文档与实现不一致

---

## 二、测试工程师 2：集成与边界

### 2.1 CloudBridge connect_relay

- 使用 `p2p::relay::connect_via_relay`，与 DESIGN 中「或等价接口」一致 ✓

### 2.2 setup P2pClientConfig

- `..Default::default()` 正确继承 connect_strategy、relay_url、punch_timeout ✓

### 2.3 发现

- **setup 注释**：仍写「p2p::hole_punch + tunnel」，未提及 relay
- **vnc_proxy 注释**：仍写「p2p::hole_punch」，relay 已独立为 relay.rs

---

## 三、测试工程师 3：错误处理与健壮性

### 3.1 Phase 3/4 已修复项

- connect_via_relay 超时、handshake 超时 ✓
- relay session TTL、auth device_id URL 编码 ✓
- relay_url_override 空串过滤 ✓（Phase 4 审查已修复）

### 3.2 无新问题

---

## 四、测试工程师 4：文档与可维护性

### 4.1 模块文档

| 文件 | 问题 |
|------|------|
| p2p/src/lib.rs | 模块列表缺 relay |
| setup.rs | 注释未提 relay |
| vnc_proxy.rs | 注释仍写 hole_punch，未提 relay |

### 4.2 PHASE1-2-3-REVIEW 状态

- 已合并到本报告，ConnectStrategy 现已接入 ✓

---

## 五、修复清单

| 问题 | 文件 | 操作 |
|------|------|------|
| p2p 模块列表缺 relay | p2p/src/lib.rs | 补充 relay |
| setup 注释过时 | setup.rs | 增加 relay |
| vnc_proxy 注释过时 | vnc_proxy.rs | 增加 relay |
| lookup None/Err 注释不准确 | p2p/src/client.rs | 改为「None 或 Err」 |

---

## 六、已知限制（不修复）

- device_id 双轨（mDNS UUID vs P2P Ed25519）
- p2p_setup_error 的 device_id 与前端展示可能不一致
- run_registry_loop 首次 3 次重试后仍失败，循环继续
