# NovAIC 系统设计总览

> 版本：2026-03-08  
> 状态：部分已实现，部分设计中

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户 macOS 桌面                               │
│                                                                     │
│  NovAIC.app (Tauri)                                                 │
│  ┌──────────────────────────────────────────────┐                  │
│  │  前端 React/Vite（三层架构）                  │                  │
│  │  Render → Business → DB/Gateway              │                  │
│  └──────────────────────────────────────────────┘                  │
│  ┌──────────────────────────────────────────────┐                  │
│  │  Rust 层（Tauri Commands）                   │                  │
│  │  • JWT 管理、文件代理、认证请求              │                  │
│  └──────────────────────────────────────────────┘                  │
│  ┌──────────────────────────────────────────────┐                  │
│  │  VmControl（embedded axum server）           │                  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐ │                  │
│  │  │ QEMU VM  │  │ AVD/ADB  │  │CloudBridge │ │                  │
│  │  │  (QMP)   │  │ (scrcpy) │  │  (WS→GW)  │ │                  │
│  │  └──────────┘  └──────────┘  └────────────┘ │                  │
│  └──────────────────────────────────────────────┘                  │
│                                                                     │
│  p2p crate（独立 workspace crate，待实现）                          │
│  • mDNS 本地发现                                                    │
│  • QUIC UDP hole punching（quinn）                                  │
│  • E2E 加密（Ed25519 设备 ID + ChaCha20）                           │
└─────────────────────────────────────────────────────────────────────┘
                │  HTTPS/WSS                │  P2P QUIC
                ▼                           ▼
┌─────────────────────────────┐    ┌─────────────────────┐
│  云端 api.gradievo.com      │    │  移动端 NovAIC App   │
│  Nginx (443)                │    │  (Tauri Mobile)      │
│  └─ JWT 验证 → X-User-ID   │    │  • P2P 客户端        │
│  Gateway (FastAPI :19999)   │    │  • WS↔隧道协议转换   │
│  ├─ REST / SSE API          │    └─────────────────────┘
│  ├─ CloudBridge WS           │
│  ├─ P2P Rendezvous（待实现）  │
│  └─ SQLite gateway.db        │
└─────────────────────────────┘
```

---

## 二、前端三层架构

### 分层原则

```
components/（渲染层）
    ↓ 只能 import
app/（业务层）
    ↓ 只能 import
db/ + gateway/（数据层）
    ↓
types/（类型定义）
```

**严禁反向依赖。components 不得直接 import gateway 或 db。**

### 各层职责

| 层 | 位置 | 职责 | 禁止 |
|---|---|---|---|
| **Render** | `components/` | 纯渲染，调用 hooks | 直接调用 gateway、db |
| **Business** | `app/` | 业务编排，协调 gateway+db | 直接操作 DOM |
| **DB** | `db/` | IndexedDB CRUD | 知道 Zustand 存在 |
| **Gateway** | `gateway/` | HTTP/SSE 通信 | 做业务判断 |
| **Rust Bridge** | Tauri commands | 认证请求、文件操作、JWT | — |

### Hooks 桥接层（components ↔ app）

```
useMessages     → messageService
useLogs         → logService  
useAgent        → agentService（含 updateVmConfig）
useSettings     → settingsService
useScrollPagination → useVirtualList（虚拟列表 + 滚动补偿）
useAuthenticatedImage → Tauri fetch_authenticated_bytes + IndexedDB 缓存
```

### 文件本地缓存策略

- **图片（Blob）**：通过 `fetch_authenticated_bytes`（Rust 命令）拉取，存入 IndexedDB `files` 对象仓库，转成 `objectURL` 给 `<img>` 使用
- **下载文件（路径）**：`local_path` 存入 IndexedDB，下次直接用本地路径打开，不重复下载
- **请求去重**：模块级 `_inFlight: Map<string, Promise<Blob>>` 防止并发重复请求

### 消息列表平滑滚动（已实现）

| 问题 | 解法 |
|---|---|
| 加载指示器插入 DOM 引发布局偏移 | 改为虚拟列表第 0 项（不占真实 DOM） |
| `requestAnimationFrame` 异步补偿导致闪跳 | 改用 `useLayoutEffect` 同步补偿 `scrollTop += Δsize` |
| 追加项目测量误差累积 | `getItemKey`（消息 ID）稳定测量 + `shouldAdjustScrollPositionOnItemSizeChange` 自动微调 |

---

## 三、Rust 层职责

位置：`novaic-app/src-tauri/src/`

| 职责 | 实现 |
|---|---|
| JWT 存储与刷新 | `CloudTokenState`，定时 proactive refresh |
| 认证 HTTP 请求 | `fetch_authenticated_bytes`：注入 Bearer token，返回原始字节，**不经过浏览器网络面板** |
| 文件下载 | `download_file_to_cache`：下载后返回本地路径 |
| 文件操作 | `open_file`、`show_in_folder` |
| 进程守护 | PID 文件、panic hook，防止重复启动 |
| VmControl 生命周期 | 启动 `VmControlEmbedded`，传入 `CloudBridgeConfig` |
| Cloud Token 更新 | `update_cloud_token` 命令，前端登录后调用 |

**认证图片加载链路：**

```
React <img>
  └─ useAuthenticatedImage(url)
       └─ IndexedDB hit? → objectURL（缓存命中）
       └─ invoke('fetch_authenticated_bytes')
            └─ Rust: reqwest + Bearer token → bytes
                 └─ 存入 IndexedDB → objectURL
```

---

## 四、VmControl + CloudBridge（已统一）

位置：`novaic-app/src-tauri/vmcontrol/`

### 职责

VmControl 是内嵌的本地 HTTP 服务器（axum），提供：

| 模块 | 功能 |
|---|---|
| `qemu/` | 通过 QMP socket 管理 QEMU Linux VM（启停/快照/状态） |
| `android/` | AVD 创建/删除，模拟器启停，scrcpy 代理 |
| `vnc/` | VNC WebSocket 代理（给前端 noVNC 使用） |
| `scrcpy/` | scrcpy 原始 TCP 代理 |
| `cloud_bridge/` | WebSocket 客户端，连接 Gateway，透明转发 Agent 控制指令到本地 VmControl HTTP |

### CloudBridge 内嵌设计

```
Gateway
  │  WS /internal/pc/ws
  │  { type: "proxy_request", method, path, body }
  ▼
cloud_bridge.rs（vmcontrol 内部 task）
  │  HTTP forward → 127.0.0.1:{vmcontrol_port}
  ▼
axum routes（vm/android/health）
  │  proxy_response → Gateway WS
  ▼
Gateway → Tools Server
```

**关键设计决策：**
- CloudBridge 与 VmControl 在**同一 Rust 进程**，无网络跨进程调用，延迟极低
- `start_embedded_server(cloud_config: Option<CloudBridgeConfig>)` 统一生命周期，CloudBridge 随 VmControl 一起启停

### 待做：Cloud Bridge + 登录时序

当前问题：App 启动时 CloudBridge 在用户登录前就尝试连接，使用空 token 反复失败。

设计方案（未实现）：
```rust
// main.rs 在 update_cloud_token 被调用时发信号
static LOGIN_NOTIFY: tokio::sync::Notify = ...;

// cloud_bridge.rs 等待登录信号再开始连接
LOGIN_NOTIFY.notified().await;
// 然后再建立 WS 连接
```

---

## 五、Gateway 设备管理（多用户改造）

### 当前问题（已识别，待实现）

| 问题 | 原因 |
|---|---|
| 全局单例 `_manager` | 多用户互相覆盖连接 |
| per-user 单连接（MULTI_USER_DESIGN 方案） | 同一用户多台 PC 时踢掉旧连接 |
| 无 `vm_id → PC` 映射 | Agent 控制 VM 时无法路由到正确 PC |
| P2P device_id 和 CloudBridge 连接身份分离 | 无法将两条路径关联到同一物理设备 |

### 目标模型：以 device_id 为核心

```python
# 统一设备注册表
_devices: Dict[str, DeviceState] = {}  # device_id → DeviceState

@dataclass
class DeviceState:
    user_id: str
    ws: Optional[WebSocket]       # CloudBridge 连接（Agent 控制路径）
    ext_ip: Optional[str]         # P2P 外网地址
    ext_port: Optional[int]
    online: bool                   # 是否开放 Agent 控制
    vm_ids: Set[str]              # 该设备托管的 VM/AVD
    last_seen: datetime
```

### 路由逻辑

```
Agent 要操控 vm-abc
  → DB 查 vms 表：vm-abc.device_id = "device-xyz"
  → _devices["device-xyz"].ws → forward_request(method, path, body)
  
用户远控 VM（P2P）
  → /api/p2p/locate?device_id=device-xyz
  → 返回 ext_ip:ext_port（供移动端建立 QUIC 连接）
```

### CloudBridge WS 握手改动

```python
# Rust 侧：连接时携带 device_id header
headers["x-device-id"] = device_id  # VmControl 启动时生成的持久 UUID

# Gateway 侧：
@router.websocket("/pc/ws")
async def pc_client_websocket(websocket: WebSocket):
    user_id = websocket.headers.get("x-user-id")   # nginx 注入
    device_id = websocket.headers.get("x-device-id")  # VmControl 上报
    manager = get_or_create_device(user_id, device_id)
    await websocket.accept()
    ...
```

### DB Schema 改动（叠加在多用户 v44 之上）

```sql
-- v45 新增
ALTER TABLE vms ADD COLUMN device_id TEXT;
CREATE TABLE devices (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    name        TEXT,
    online      INTEGER NOT NULL DEFAULT 0,
    last_seen   TEXT,
    created_at  TEXT
);
CREATE INDEX idx_devices_user_id ON devices(user_id);
```

---

## 六、P2P 远控架构（设计中，待实现）

### 场景

用户用手机/平板远程控制 PC 上的 VM（VNC）或 Android 模拟器（scrcpy）。  
链路：`移动端 App → P2P QUIC 隧道 → VmControl`

### 连接策略

| 场景 | 方案 |
|---|---|
| **同 LAN** | mDNS 发现 → 直连 TCP（无隧道） |
| **跨网络（NAT）** | QUIC UDP hole punching（quinn 库） |
| **hole punching 失败** | 报错，**不使用 relay**（避免延迟） |

### 核心组件

```
p2p/（新 workspace crate，VmControl 和 Tauri Mobile 共用）
├── local_discovery.rs    mDNS 广播/发现（mdns-sd 库）
├── device_id.rs          Ed25519 密钥对，公钥即设备 ID，持久化存 data_dir
├── rendezvous.rs         向 Gateway rendezvous 注册心跳，NAT 打洞协调
├── hole_punch.rs         QUIC UDP hole punching（quinn）
├── tunnel.rs             QUIC 流复用：VNC 和 scrcpy 透明代理
└── crypto.rs             X25519 握手 + ChaCha20-Poly1305 E2E 加密
```

### 连接建立流程

**本地 LAN（mDNS）：**
```
PC VmControl 广播 _novaic._tcp.local
  → 移动端 mDNS 发现 → 直接 TCP 连接 :vmcontrol_port
  → TLS 握手（Ed25519 验证设备身份）
  → VNC/scrcpy 透明代理
```

**远程 P2P（QUIC）：**
```
双端定期向 Gateway POST /api/p2p/heartbeat { device_id, ext_ip, ext_port }
  → 移动端请求 GET /api/p2p/locate?device_id=xxx → 获得 PC ext_ip:port
  → 双端同时向对方发 QUIC 握手包（打洞）
  → 打洞成功 → QUIC 连接建立（TLS 1.3 内置，无需额外加密层）
  → 在 QUIC 流上复用 VNC stream / scrcpy stream
```

### 数据流

```
移动端 App
  └─ Tauri Rust（P2P 客户端）
       └─ WebSocket（来自前端 JS noVNC/scrcpy-web）
            ↔
       QUIC stream（P2P 隧道）
            ↕
PC VmControl（tunnel.rs）
  └─ 本地 VNC :5900 / scrcpy ADB
```

### 安全模型

| 机制 | 实现 |
|---|---|
| 设备身份 | Ed25519 keypair，公钥 = device_id，私钥本地不出 |
| 传输加密 | QUIC/TLS 1.3（quinn 默认），无需额外层 |
| 访问控制 | Gateway 校验 `device_id` 归属 `user_id`，locate 接口鉴权 |
| 无中间人 | 直连，无 relay，无法在 Gateway 侧解密流量 |

---

## 七、多用户改造（设计文档 MULTI_USER_DESIGN.md）

### 身份传递链

```
JWT（前端 localStorage）
  → Authorization: Bearer <jwt>
    → nginx: 验证 HS256，解出 user_id
      → proxy_set_header X-User-ID $jwt_user_id
        → Gateway: 所有路由通过 Depends(get_current_user) 获取 user_id
```

### DB 改动（v43 → v44 → v45）

| 版本 | 改动 |
|---|---|
| v44 | `agents`、`api_keys`、`ssh_keys`、`config`、`candidate_models` 加 `user_id` |
| v45 | 新增 `devices` 表，`vms` 表加 `device_id` |

### Gateway `PcClientManager` 改造路线

```
v1（现在）：全局单例 _manager
v2（MULTI_USER_DESIGN）：per-user Dict[user_id → PcClientManager]  ← 不够
v3（目标）：per-device Dict[device_id → DeviceState]               ← 正确
```

---

## 八、已实现 vs 待实现

| 模块 | 状态 | 位置 |
|---|---|---|
| 前端三层架构 | ✅ 已实现 | `novaic-app/src/` |
| useAuthenticatedImage + Rust fetch | ✅ 已实现 | `src/components/hooks/useAuthenticatedImage.ts` |
| 消息列表平滑滚动 | ✅ 已实现 | `useScrollPagination.ts` + `MessageList.tsx` |
| VmControl + CloudBridge 统一 | ✅ 已实现 | `vmcontrol/src/cloud_bridge.rs` |
| CloudBridge 登录时序优化 | ⏳ 待实现 | `main.rs` + `cloud_bridge.rs` |
| 多用户 Gateway 改造（v44） | ⏳ 待实现 | `novaic-gateway/` |
| device_id 统一（v45） | ⏳ 待实现 | `pc_client.py` + DB |
| VmControl 持久 device_id | ⏳ 待实现 | `vmcontrol/src/config.rs` |
| P2P crate（local_discovery） | ⏳ 待实现 | `p2p/src/local_discovery.rs` |
| P2P rendezvous + hole punch | ⏳ 待实现 | `p2p/src/rendezvous.rs` |
| P2P QUIC 隧道（VNC/scrcpy） | ⏳ 待实现 | `p2p/src/tunnel.rs` |
| Gateway P2P API | ⏳ 待实现 | `novaic-gateway/api/p2p.py` |

---

## 九、推荐实现顺序

```
Phase 1：设备身份基础
  1. VmControl 生成持久 device_id（Ed25519 keypair）
  2. CloudBridge 连接时携带 x-device-id header
  3. Gateway pc_client.py 改为 per-device DeviceState

Phase 2：P2P 本地发现
  4. p2p crate 初始化（workspace crate）
  5. local_discovery.rs（mDNS 广播 + 发现）
  6. 同 LAN 直连 VNC/scrcpy

Phase 3：P2P 远程打洞
  7. rendezvous.rs（Gateway 心跳注册）
  8. Gateway /api/p2p/* API
  9. hole_punch.rs（QUIC UDP 打洞）
  10. tunnel.rs（QUIC 流复用代理）

Phase 4：多用户
  11. DB v44 migration（user_id 隔离）
  12. Gateway 路由加 ownership 校验
  13. DB v45 migration（devices 表）
  14. App 登录 UI + JWT 流程
```
