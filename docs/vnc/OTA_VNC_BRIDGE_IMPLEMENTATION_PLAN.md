# OTA 模式 VNC Tauri Bridge 实施方案

> 方案 1：通过 Tauri IPC 桥接 noVNC 与 VncProxy，解决 OTA 模式下 HTTPS 页面无法连接 ws:// 的 Mixed Content 问题。

---

## 一、目标与约束

### 目标
- OTA 模式下 VNC 可正常连接（页面来自 `https://relay.gradievo.com`）
- 本地模式保持现有行为（直接 `new WebSocket(url)`）
- 不改动 VncProxy 和 noVNC 核心逻辑

### 约束
- noVNC RFB 支持传入 WebSocket 实例或兼容对象（需 `send`、`close`、`onopen`、`onmessage`、`readyState` 等）
- 运行时根据 `location.origin` 判断是否 OTA，动态选择 URL 或 Bridge

---

## 二、架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 前端 (WebView)                                                           │
│                                                                         │
│  本地模式:  new RFB(container, wsUrl)     → new WebSocket(wsUrl)        │
│            ↑ 直接连接，无 Mixed Content                                   │
│                                                                         │
│  OTA 模式:  new RFB(container, VncBridgeTransport)                       │
│            ↑ 假 WebSocket，底层走 Tauri IPC                              │
│            VncBridgeTransport.send(data) → invoke('vnc_bridge_send')     │
│            listen('vnc_bridge:data')      → onmessage                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ invoke / emit
┌─────────────────────────────────────────────────────────────────────────┐
│ Rust 后端                                                                │
│                                                                         │
│  vnc_bridge_connect(agentId, deviceId)                                   │
│    → 解析 device_id（复用 get_vnc_proxy_url 逻辑）                        │
│    → tokio_tungstenite::connect_async(ws://127.0.0.1:port/vnc/...)       │
│    → 生成 bridge_id (UUID)                                              │
│    → spawn 桥接任务: WS ↔ emit/invoke                                     │
│    → 返回 bridge_id                                                      │
│                                                                         │
│  vnc_bridge_send(bridge_id, data)                                        │
│    → 查找 bridge，转发到 WebSocket                                       │
│                                                                         │
│  vnc_bridge_close(bridge_id)                                            │
│    → 关闭 WebSocket，清理 bridge 状态                                     │
│                                                                         │
│  emit('vnc_bridge:{bridge_id}:data', base64(data))  ← WebSocket 收到数据  │
│  emit('vnc_bridge:{bridge_id}:close', reason)       ← 连接关闭           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ WebSocket 客户端
┌─────────────────────────────────────────────────────────────────────────┐
│ VncProxy (ws://127.0.0.1:port) — 无需改动                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、文件改动清单

### 3.1 新增文件

| 文件 | 说明 |
|------|------|
| `novaic-app/src/services/vncBridge.ts` | `VncBridgeTransport` 类，实现 WebSocket 兼容接口 |
| `novaic-app/src-tauri/src/commands/vnc_bridge.rs` | Rust 桥接命令与状态管理 |

### 3.2 修改文件

| 文件 | 改动 |
|------|------|
| `novaic-app/src-tauri/Cargo.toml` | 移动端增加 `tokio-tungstenite` 依赖 |
| `novaic-app/src-tauri/src/commands/mod.rs` | 注册 `vnc_bridge` 模块 |
| `novaic-app/src-tauri/src/lib.rs` | 注册 `vnc_bridge_connect`、`vnc_bridge_send`、`vnc_bridge_close` 命令 |
| `novaic-app/src-tauri/permissions/allow-app-commands.toml` | 增加上述命令权限 |
| `novaic-app/src-tauri/capabilities/remote-frontend.json` | 确保 OTA 下可调用（已有 allow-app-commands） |
| `novaic-app/src/services/vm.ts` | 新增 `getVncTransport(agentId, deviceId)`，按 OTA 返回 URL 或 Bridge |
| `novaic-app/src/config/index.ts` | 新增 `isOtaOrigin()` 工具函数（或复用现有 `OTA_ORIGINS`） |
| `novaic-app/src/components/VM/VmUserVNCView.tsx` | 使用 `getVncTransport`，支持 URL 或 Transport |
| `novaic-app/src/components/Visual/DeviceVNCView.tsx` | 同上 |
| `novaic-app/src/services/vncStream.ts` | 同上 |
| `novaic-app/src/components/Visual/useVNCConnection.ts` | `checkWebSocket` 在 OTA 下改为检测 Bridge 可用性 |
| `novaic-app/src/components/Visual/useDeviceVNCConnection.ts` | 同上 |

---

## 四、详细实现步骤

### Phase 1：Rust 桥接层

#### 4.1.1 依赖

**Cargo.toml**：移动端增加 tokio-tungstenite（桥接需 WebSocket 客户端）

```toml
# 在 [target.'cfg(any(target_os = "android", target_os = "ios"))'.dependencies] 中增加：
tokio-tungstenite = { version = "0.24", default-features = false, features = ["rustls-tls-native-roots"] }
```

> 注：p2p 使用 0.21，主 crate 用 0.24 需确认兼容；若有冲突可统一版本。

#### 4.1.2 桥接状态

**vnc_bridge.rs** 核心结构：

```rust
// 全局 bridge 注册表：bridge_id -> (tx_send, join_handle)
// tx_send: 用于 vnc_bridge_send 向桥接任务发送数据
// join_handle: 桥接任务句柄，用于关闭时 abort
use std::collections::HashMap;
use tokio::sync::{mpsc, RwLock};

struct BridgeState {
    bridges: RwLock<HashMap<String, BridgeHandle>>,
}

struct BridgeHandle {
    tx: mpsc::Sender<Vec<u8>>,  // 前端 → WebSocket
    _join: tokio::task::JoinHandle<()>,
}
```

#### 4.1.3 命令 `vnc_bridge_connect`

**签名**：
```rust
#[tauri::command]
pub async fn vnc_bridge_connect(
    proxy: State<'_, VncProxyState>,
    gw_url: State<'_, GatewayUrlState>,
    cloud_token: State<'_, CloudTokenState>,
    app: AppHandle,
    agentId: String,
    deviceId: Option<String>,
) -> Result<String, String>
```

**逻辑**：
1. 复用 `get_vnc_proxy_url` 的 device_id 解析（可提取为共享函数 `resolve_device_and_agent_id`）
2. 获取 `ws_url = p.ws_url(&device_id, &agent_id)`
3. 生成 `bridge_id = uuid::Uuid::new_v4().to_string()`
4. `tokio_tungstenite::connect_async(ws_url)` 连接 VncProxy
5. 创建 `mpsc::channel::<Vec<u8>>(64)` 用于前端发送
6. `spawn` 桥接任务：
   - 收：`ws.next()` → `app.emit("vnc_bridge:{bridge_id}:data", base64::encode(data))`
   - 收：`Close` → `app.emit("vnc_bridge:{bridge_id}:close", reason)`，从注册表移除
   - 发：`rx.recv()` → `ws.send(Message::Binary(data))`
7. 将 `(tx, join_handle)` 存入 `BridgeState`
8. 返回 `bridge_id`

**错误处理**：连接失败时返回 `Err(msg)`，不创建 bridge。

#### 4.1.4 命令 `vnc_bridge_send`

**签名**：
```rust
#[tauri::command]
pub async fn vnc_bridge_send(
    bridge_state: State<'_, BridgeState>,
    bridgeId: String,
    data: Vec<u8>,  // 或使用 Tauri 2 的 Raw binary
) -> Result<(), String>
```

**逻辑**：从 `bridge_state.bridges` 取 `tx`，`tx.send(data).await`。若 bridge 不存在返回 `Err`。

> 数据格式：前端可传 `ArrayBuffer`/`Uint8Array`，Tauri 2 支持；或 base64 字符串。优先尝试 binary。

#### 4.1.5 命令 `vnc_bridge_close`

**签名**：
```rust
#[tauri::command]
pub async fn vnc_bridge_close(
    bridge_state: State<'_, BridgeState>,
    bridgeId: String,
) -> Result<(), String>
```

**逻辑**：从注册表移除，`drop(tx)` 使桥接任务退出，`join.abort()`（如需要）。

---

### Phase 2：前端 VncBridgeTransport

#### 4.2.1 `VncBridgeTransport` 类

**vncBridge.ts**：

```typescript
// 实现 WebSocket 兼容接口，供 noVNC RFB 使用
// 需实现：readyState, binaryType, send(data), close(), onopen, onmessage, onerror, onclose

export class VncBridgeTransport {
  readonly CONNECTING = 0;
  readonly OPEN = 1;
  readonly CLOSING = 2;
  readonly CLOSED = 3;

  readyState = 0;
  binaryType: 'arraybuffer' | 'blob' = 'arraybuffer';

  onopen: (() => void) | null = null;
  onmessage: ((e: { data: ArrayBuffer | string }) => void) | null = null;
  onerror: ((e: unknown) => void) | null = null;
  onclose: ((e: { code?: number; reason?: string }) => void) | null = null;

  private bridgeId: string | null = null;
  private unlistenData: (() => void) | null = null;
  private unlistenClose: (() => void) | null = null;

  constructor(
    private agentId: string,
    private deviceId?: string
  ) {}

  async connect(): Promise<void> {
    this.readyState = this.CONNECTING;
    try {
      this.bridgeId = await invoke<string>('vnc_bridge_connect', {
        agentId: this.agentId,
        deviceId: this.deviceId ?? null,
      });
      this.readyState = this.OPEN;
      this.setupListeners();
      this.onopen?.();
    } catch (e) {
      this.readyState = this.CLOSED;
      this.onerror?.(e);
      this.onclose?.({ code: 1011, reason: String(e) });
    }
  }

  private setupListeners(): void {
    if (!this.bridgeId) return;
    const dataEvent = `vnc_bridge:${this.bridgeId}:data`;
    const closeEvent = `vnc_bridge:${this.bridgeId}:close`;
    this.unlistenData = await listen<string>(dataEvent, (e) => {
      const buf = base64ToArrayBuffer(e.payload);
      this.onmessage?.({ data: buf });
    });
    this.unlistenClose = await listen<string>(closeEvent, (e) => {
      this.cleanup();
      this.readyState = this.CLOSED;
      this.onclose?.({ reason: e.payload });
    });
  }

  send(data: ArrayBuffer | string): void {
    if (this.readyState !== this.OPEN || !this.bridgeId) return;
    const bytes = typeof data === 'string' ? new TextEncoder().encode(data) : new Uint8Array(data);
    invoke('vnc_bridge_send', { bridgeId: this.bridgeId, data: Array.from(bytes) });
    // 或使用 Tauri 2 binary: invoke('vnc_bridge_send', bytes, { headers: { ... } })
  }

  close(): void {
    if (this.readyState === this.CLOSED || this.CLOSING) return;
    this.readyState = this.CLOSING;
    if (this.bridgeId) {
      invoke('vnc_bridge_close', { bridgeId: this.bridgeId });
    }
    this.cleanup();
    this.readyState = this.CLOSED;
    this.onclose?.({});
  }

  private cleanup(): void {
    this.unlistenData?.();
    this.unlistenClose?.();
    this.unlistenData = null;
    this.unlistenClose = null;
    this.bridgeId = null;
  }
}
```

> 注意：noVNC 可能在 `connect` 完成前就调用 `send`，需在 `readyState === OPEN` 前缓冲或忽略。

#### 4.2.2 OTA 检测

**config/index.ts** 或 **vncBridge.ts**：

```typescript
import { OTA_ORIGINS } from '../config';

export function isOtaOrigin(): boolean {
  if (typeof location === 'undefined') return false;
  return OTA_ORIGINS.some((o) => location.origin === o);
}
```

---

### Phase 3：vmService 统一入口

#### 4.3.1 `getVncTransport`

**vm.ts**：

```typescript
/**
 * 获取 VNC 传输：OTA 模式返回 VncBridgeTransport，否则返回 WebSocket URL。
 * RFB 支持 string | WebSocket，调用方根据类型创建 RFB。
 */
async getVncTransport(
  agentId: string,
  deviceId?: string
): Promise<string | VncBridgeTransport> {
  if (isOtaOrigin()) {
    const transport = new VncBridgeTransport(agentId, deviceId);
    await transport.connect();
    return transport;
  }
  return this.getVncUrl(agentId, deviceId);
}
```

> 注意：`VncBridgeTransport.connect()` 是 async，而 `getVncUrl` 返回的 URL 是同步可用的。RFB 对 WebSocket 期望「传入时已连接或正在连接」。若传入 `VncBridgeTransport`，需在 `connect()` 完成后再传给 RFB，因此 `getVncTransport` 设计为 async 且 OTA 时 await connect。

---

### Phase 4：组件适配

#### 4.4.1 VmUserVNCView

当前：
```ts
wsUrl = await vmService.getVncUrl(`${deviceId}:${username}`);
const rfb = new RFB(canvasRef.current, wsUrl, { wsProtocols: ['binary'] });
```

改为：
```ts
const transport = await vmService.getVncTransport(`${deviceId}:${username}`);
const rfb = new RFB(canvasRef.current, transport, { wsProtocols: ['binary'] });
```

#### 4.4.2 DeviceVNCView

当前依赖 `useDeviceVNCConnection` 返回 `wsUrl`，再 `new RFB(..., wsUrl, ...)`。

需改为：
- `useDeviceVNCConnection` 在 OTA 下返回 `transport: VncBridgeTransport | null` 而非 `wsUrl`
- 或：`useDeviceVNCConnection` 返回 `{ wsUrl, transport }`，调用方根据 `transport ?? wsUrl` 创建 RFB

建议：`useDeviceVNCConnection` 和 `useVNCConnection` 统一返回 `transportOrUrl: string | VncBridgeTransport | null`，调用方用 `new RFB(container, transportOrUrl, opts)`。

#### 4.4.3 vncStream.ts

`connectStream` 内：
```ts
state.wsUrl = await vmService.getVncUrl(agentId, deviceId);
// ...
const rfb = new RFB(container, state.wsUrl, { ... });
```

改为：
```ts
const transportOrUrl = await vmService.getVncTransport(agentId, deviceId);
// 存 transport 或 url，用于重连时判断
state.transportOrUrl = transportOrUrl;
const rfb = new RFB(container, transportOrUrl, { ... });
```

#### 4.4.4 useVNCConnection / useDeviceVNCConnection 的 checkWebSocket

当前：`new WebSocket(url)` 探测。

OTA 下：不能 `new WebSocket`，可改为：
- 调用 `invoke('vnc_bridge_connect', ...)` 做一次性探测，成功则立即 `vnc_bridge_close`；或
- 简化：OTA 下跳过 checkWebSocket，直接认为「可用」，由 RFB 连接失败时再处理。

建议：OTA 下 `checkWebSocket` 调用 `getVncTransport`，若返回 `VncBridgeTransport` 则视为可用（因 connect 已成功），然后 close 该 transport，避免占用；或保留一个轻量探测命令 `vnc_bridge_probe(agentId, deviceId)` 仅做连接测试。

---

### Phase 5：权限与 Capability

- `allow-app-commands.toml`：增加 `vnc_bridge_connect`、`vnc_bridge_send`、`vnc_bridge_close`
- `remote-frontend.json`：已包含 `allow-app-commands`，无需改
- `core:event:allow-listen`：前端需 listen 事件，确认 capability 已包含（main-cap 或 remote-frontend）

---

## 五、数据流与性能

### 5.1 数据量估算

| 方向 | 典型量 | 频率 |
|------|--------|------|
| VncProxy → 前端 | 10–100 KB/帧 | 10–30 FPS |
| 前端 → VncProxy | 输入事件，< 1 KB | 按需 |

### 5.2 IPC 开销

- `emit`  payload：base64 编码，约 +33% 体积
- 每帧一次 `emit`：需验证 Tauri 事件吞吐与延迟
- 若卡顿：可考虑分块（如 16KB/块）、或后续探索 Tauri 2 的 binary event（若支持）

### 5.3 优化方向（后续）

1. 大帧分块 emit，前端重组
2. 使用 Tauri 2 的 raw binary IPC（若 event 支持）
3. 前端对 RFB 做帧率/画质调节，降低带宽

---

## 六、测试计划

### 6.1 单元 / 集成

| 场景 | 步骤 | 预期 |
|------|------|------|
| 本地 + URL | 关闭 OTA，加载本地 | VNC 正常，与现有一致 |
| OTA + Bridge | 启用 OTA，加载 relay | VNC 通过 Bridge 正常 |
| 多 Agent | OTA 下开多个 VNC | 每个独立 bridge_id，互不干扰 |
| 断线 | Bridge 连接后 VncProxy 断开 | 收到 close 事件，UI 显示断开 |

### 6.2 手动验证

1. `NOVAIC_OTA_ENABLED=1` 启动 App
2. 确认页面来自 `https://relay.gradievo.com`
3. 打开 VNC 视图，确认连接成功
4. 操作桌面，确认无明显延迟或花屏

---

## 七、回滚计划

- 所有改动通过 `isOtaOrigin()` 门控，仅在 OTA 下走 Bridge
- 若 Bridge 有问题，可临时 `isOtaOrigin = () => false`，强制全部走 URL（OTA 下 VNC 会继续失败，但可快速回退）

---

## 八、实施顺序建议

1. **Phase 1**：Rust 桥接层（vnc_bridge.rs、命令、权限）
2. **Phase 2**：VncBridgeTransport 与基础连通性测试
3. **Phase 3**：vmService.getVncTransport
4. **Phase 4**：逐个组件适配（VmUserVNCView → DeviceVNCView → vncStream → hooks）
5. **Phase 5**：权限与 capability 检查
6. **Phase 6**：完整测试与性能调优

---

## 九、附录：noVNC RFB 兼容接口

根据 noVNC 源码，传入对象需满足（或可 duck-type）：

- `readyState`: 0 | 1 | 2 | 3
- `binaryType`: 'arraybuffer' | 'blob'
- `send(data: ArrayBuffer | string)`
- `close()`
- `onopen`, `onmessage`, `onerror`, `onclose` 回调

无需实现 `addEventListener`，noVNC 通过上述属性使用。
