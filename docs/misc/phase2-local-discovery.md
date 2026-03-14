# Phase 2 — P2P 本地发现（Local Network Discovery）

> 目标：移动端 App 在同一局域网内自动发现 PC 上的 VmControl，  
> 无需手动输入 IP，直接建立低延迟 TCP/WebSocket 连接进行 VNC/scrcpy 控制。  
> 本阶段不涉及跨网络（NAT）场景，那是 Phase 3 的任务。

---

## 一、背景与场景

### 核心场景

```
家庭 / 办公室 WiFi 同一 LAN：
  手机 NovAIC App  ←→  WiFi Router  ←→  PC NovAIC App（VmControl）
```

用户打开手机 App → 自动发现局域网内 PC → 点击连接 → 直接控制 VM/AVD，**零配置，零延迟（LAN 内 <2ms）**。

### 为什么需要独立 Phase

- mDNS 在 iOS/Android 有系统权限要求（Bonjour/NSD），需要单独处理
- LAN 直连路径和 P2P QUIC 路径**并行存在**，LAN 时优先用直连，代码需要分层
- 本阶段可以在没有 Phase 3（QUIC 打洞）的情况下独立交付价值

---

## 二、技术选型

| 方案 | 优点 | 缺点 |
|---|---|---|
| **mDNS（_novaic._tcp.local）** | 跨平台、零配置、系统级支持 | iOS 需要 `NSBonjourServices` 配置 |
| UDP 广播 | 简单 | 部分路由器禁止广播转发 |
| 固定 IP 手动输入 | 无需实现 | 用户体验差，非本场景目标 |

**选择：mDNS**，使用 `mdns-sd` crate（Rust），iOS/Android 通过 Tauri Mobile 的 mDNS API。

---

## 三、Workspace Crate 结构

Phase 2 引入独立的 `p2p` workspace crate，供 VmControl（PC）和 Tauri Mobile（移动端）共用。

```
novaic-app/src-tauri/
├── Cargo.toml              # workspace members 增加 "p2p"
├── p2p/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── device_id.rs    # Phase 2 新增：Ed25519 keypair（Phase 1 的 UUID 升级版）
│       ├── local_discovery.rs   # Phase 2 核心：mDNS 广播与发现
│       └── types.rs        # 共用类型定义
├── vmcontrol/
└── src/                    # Tauri 主进程
```

---

## 四、P2P Crate 初始化

### Cargo.toml

**文件：** `novaic-app/src-tauri/p2p/Cargo.toml`

```toml
[package]
name = "p2p"
version = "0.1.0"
edition = "2021"

[dependencies]
# mDNS 服务发现
mdns-sd = "0.11"

# 异步运行时
tokio = { version = "1", features = ["full"] }
tokio-util = { version = "0.7", features = ["codec"] }

# 序列化
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Ed25519 密钥对（Phase 3 准备，Phase 2 也用于设备 ID）
ed25519-dalek = { version = "2", features = ["rand_core"] }
rand = "0.8"

# 日志
tracing = "0.1"

# 工具
uuid = { version = "1", features = ["v4"] }
hex = "0.4"
thiserror = "1"
```

### Workspace Cargo.toml 改动

**文件：** `novaic-app/src-tauri/Cargo.toml`

```toml
[workspace]
members = [
    ".",
    "vmcontrol",
    "p2p",         # 新增
]
```

---

## 五、types.rs — 共用类型

**文件：** `novaic-app/src-tauri/p2p/src/types.rs`

```rust
use serde::{Deserialize, Serialize};

/// VmControl 在 LAN 内广播的服务信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VmControlService {
    /// 设备唯一 ID（同 Phase 1 device_id）
    pub device_id: String,
    /// VmControl HTTP 服务端口
    pub http_port: u16,
    /// VNC WebSocket 代理端口
    pub vnc_port: Option<u16>,
    /// scrcpy TCP 代理端口
    pub scrcpy_port: Option<u16>,
    /// 主机名（可读）
    pub hostname: String,
    /// 设备友好名称（用户设置）
    pub display_name: Option<String>,
}

/// 发现事件
#[derive(Debug, Clone)]
pub enum DiscoveryEvent {
    /// 发现新设备
    Discovered(VmControlService),
    /// 设备下线
    Removed(String),  // device_id
}
```

---

## 六、device_id.rs — 设备 ID 升级（UUID → Ed25519）

> Phase 1 使用 UUID v4 作为 device_id（简单）。  
> Phase 2 可选择升级为 Ed25519 公钥（与 Phase 3 P2P 加密复用同一 keypair）。  
> **兼容策略**：文件格式不变（hex string），只是生成方式改变；旧 UUID 继续有效。

**文件：** `novaic-app/src-tauri/p2p/src/device_id.rs`

```rust
//! 设备 ID 管理
//!
//! Phase 1: UUID v4（随机字符串）
//! Phase 2+: Ed25519 公钥（hex），与 P2P 加密复用同一 keypair
//!
//! 文件格式：data_dir/device_id.txt（一行 hex string）
//! keypair 文件：data_dir/device_keypair.bin（64 字节原始格式，仅 Phase 2+）

use ed25519_dalek::{SigningKey, VerifyingKey};
use rand::rngs::OsRng;
use std::path::PathBuf;
use std::fs;
use tracing::{info, warn};

pub struct DeviceIdentity {
    /// 公钥 hex，用作 device_id
    pub id: String,
    /// 签名密钥（用于 P2P 握手认证）
    pub signing_key: SigningKey,
}

impl DeviceIdentity {
    /// 从 data_dir 加载或生成设备身份。
    /// 若已有 UUID 格式的 device_id.txt，迁移为 Ed25519（生成新 keypair，更新文件）。
    pub fn load_or_generate(data_dir: &PathBuf) -> Self {
        let id_file = data_dir.join("device_id.txt");
        let key_file = data_dir.join("device_keypair.bin");

        // 尝试加载已有 keypair
        if key_file.exists() {
            if let Ok(bytes) = fs::read(&key_file) {
                if bytes.len() == 32 {
                    let key_bytes: [u8; 32] = bytes.try_into().unwrap();
                    let signing_key = SigningKey::from_bytes(&key_bytes);
                    let id = hex::encode(signing_key.verifying_key().as_bytes());
                    info!("[DeviceID] Loaded Ed25519 device_id: {}...", &id[..8]);
                    return Self { id, signing_key };
                }
            }
        }

        // 检查是否有旧 UUID（Phase 1 遗留）
        let has_old_uuid = id_file.exists();
        if has_old_uuid {
            warn!("[DeviceID] Upgrading from UUID to Ed25519 device_id");
        }

        // 生成新 Ed25519 keypair
        let signing_key = SigningKey::generate(&mut OsRng);
        let id = hex::encode(signing_key.verifying_key().as_bytes());

        // 持久化
        let _ = fs::create_dir_all(data_dir);
        let _ = fs::write(&id_file, &id);
        let _ = fs::write(&key_file, signing_key.to_bytes());
        info!("[DeviceID] Generated new Ed25519 device_id: {}...", &id[..8]);

        Self { id, signing_key }
    }

    pub fn verifying_key(&self) -> VerifyingKey {
        self.signing_key.verifying_key()
    }
}
```

---

## 七、local_discovery.rs — mDNS 核心

**文件：** `novaic-app/src-tauri/p2p/src/local_discovery.rs`

```rust
//! LAN 内 mDNS 服务发现
//!
//! PC（VmControl）端：广播 _novaic._tcp.local 服务
//! 移动端（Tauri Mobile）：监听并发现 _novaic._tcp.local 服务
//!
//! 使用 mdns-sd crate（纯 Rust 实现，无系统依赖）

use mdns_sd::{ServiceDaemon, ServiceEvent, ServiceInfo};
use std::collections::HashMap;
use tokio::sync::mpsc;
use tracing::{debug, info, warn};

use crate::types::{DiscoveryEvent, VmControlService};

const SERVICE_TYPE: &str = "_novaic._tcp.local.";
const SERVICE_SUBTYPE: &str = "_novaic._tcp.local.";

/// 广播本机 VmControl 服务到 LAN（PC 端调用）
///
/// # 参数
/// - `service`: 要广播的服务信息
/// - `shutdown`: 关闭信号
///
/// # 行为
/// - 持续广播直到收到 shutdown 信号
/// - 退出时自动注销服务（其他设备会收到 Removed 事件）
pub async fn advertise(
    service: VmControlService,
    mut shutdown: tokio::sync::oneshot::Receiver<()>,
) {
    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            warn!("[mDNS] Failed to start ServiceDaemon: {}", e);
            return;
        }
    };

    // 构建 mDNS TXT 记录，携带 VmControl 元数据
    let mut properties = HashMap::new();
    properties.insert("device_id".to_string(), service.device_id.clone());
    properties.insert("http_port".to_string(), service.http_port.to_string());
    if let Some(p) = service.vnc_port {
        properties.insert("vnc_port".to_string(), p.to_string());
    }
    if let Some(p) = service.scrcpy_port {
        properties.insert("scrcpy_port".to_string(), p.to_string());
    }
    if let Some(name) = &service.display_name {
        properties.insert("display_name".to_string(), name.clone());
    }

    // 服务实例名：device_id 前 8 位（可读且唯一）
    let instance_name = format!("novaic-{}", &service.device_id[..8.min(service.device_id.len())]);

    let service_info = match ServiceInfo::new(
        SERVICE_TYPE,
        &instance_name,
        &service.hostname,
        "",        // IP 由 mdns-sd 自动绑定到所有本机接口
        service.http_port,
        properties,
    ) {
        Ok(info) => info,
        Err(e) => {
            warn!("[mDNS] Failed to create ServiceInfo: {}", e);
            return;
        }
    };

    if let Err(e) = mdns.register(service_info) {
        warn!("[mDNS] Failed to register service: {}", e);
        return;
    }
    info!("[mDNS] Advertising VmControl as {} on port {}", instance_name, service.http_port);

    // 等待关闭信号
    let _ = shutdown.await;

    // 注销服务（通知 LAN 内其他设备）
    if let Err(e) = mdns.unregister(&format!("{}.{}", instance_name, SERVICE_TYPE)) {
        debug!("[mDNS] Unregister warning: {}", e);
    }
    let _ = mdns.shutdown();
    info!("[mDNS] mDNS advertisement stopped");
}

/// 发现 LAN 内的 VmControl 服务（移动端调用）
///
/// # 参数
/// - `tx`: 发现事件发送通道
/// - `shutdown`: 关闭信号
///
/// # 行为
/// - 持续监听，发现/消失事件通过 `tx` 通知调用方
/// - 调用方维护 device_id → VmControlService 的映射
pub async fn discover(
    tx: mpsc::Sender<DiscoveryEvent>,
    mut shutdown: tokio::sync::oneshot::Receiver<()>,
) {
    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            warn!("[mDNS] Failed to start ServiceDaemon: {}", e);
            return;
        }
    };

    let receiver = match mdns.browse(SERVICE_TYPE) {
        Ok(r) => r,
        Err(e) => {
            warn!("[mDNS] Failed to browse: {}", e);
            return;
        }
    };

    info!("[mDNS] Browsing for {} services", SERVICE_TYPE);

    loop {
        tokio::select! {
            biased;
            _ = &mut shutdown => {
                info!("[mDNS] Discovery stopped");
                let _ = mdns.shutdown();
                return;
            }
            event = async { receiver.recv_async().await } => {
                match event {
                    Ok(ServiceEvent::ServiceResolved(info)) => {
                        debug!("[mDNS] Resolved: {:?}", info.get_fullname());
                        if let Some(service) = parse_service_info(&info) {
                            info!("[mDNS] Discovered VmControl: {} @ {:?}:{}",
                                service.device_id, info.get_addresses(), service.http_port);
                            let _ = tx.send(DiscoveryEvent::Discovered(service)).await;
                        }
                    }
                    Ok(ServiceEvent::ServiceRemoved(_, fullname)) => {
                        debug!("[mDNS] Removed: {}", fullname);
                        // 从 fullname 提取 device_id（通过匹配实例名前缀）
                        if let Some(device_id) = extract_device_id_from_fullname(&fullname) {
                            let _ = tx.send(DiscoveryEvent::Removed(device_id)).await;
                        }
                    }
                    Ok(ServiceEvent::SearchStarted(_)) | Ok(ServiceEvent::SearchStopped(_)) => {}
                    Err(e) => {
                        warn!("[mDNS] Browse error: {}", e);
                        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                    }
                    _ => {}
                }
            }
        }
    }
}

fn parse_service_info(info: &ServiceInfo) -> Option<VmControlService> {
    let props = info.get_properties();
    let device_id = props.get_property_val_str("device_id")?;
    let http_port: u16 = props.get_property_val_str("http_port")
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);
    if http_port == 0 {
        return None;
    }

    // 取第一个 IP 地址
    let addresses: Vec<_> = info.get_addresses().iter().collect();
    if addresses.is_empty() {
        return None;
    }
    let hostname = addresses[0].to_string();

    Some(VmControlService {
        device_id: device_id.to_string(),
        http_port,
        vnc_port: props.get_property_val_str("vnc_port").and_then(|s| s.parse().ok()),
        scrcpy_port: props.get_property_val_str("scrcpy_port").and_then(|s| s.parse().ok()),
        hostname,
        display_name: props.get_property_val_str("display_name").map(|s| s.to_string()),
    })
}

fn extract_device_id_from_fullname(fullname: &str) -> Option<String> {
    // fullname 格式：novaic-{device_id_prefix}._novaic._tcp.local.
    // 这里用简单前缀匹配
    let instance = fullname.split('.').next()?;
    if instance.starts_with("novaic-") {
        Some(instance.trim_start_matches("novaic-").to_string())
    } else {
        None
    }
}
```

---

## 八、VmControl 集成：启动 mDNS 广播

**文件：** `novaic-app/src-tauri/vmcontrol/src/lib.rs`（在 `start_embedded_server` 中集成）

```rust
// 在 vmcontrol/Cargo.toml 中添加依赖：
// p2p = { path = "../p2p" }

// start_embedded_server 中：
pub async fn start_embedded_server(
    config: Config,
    cloud_config: Option<CloudBridgeConfig>,
    shutdown: tokio::sync::oneshot::Receiver<()>,
) {
    // ... 启动 axum 服务器（现有逻辑）...

    // 启动 mDNS 广播（新增）
    let (mdns_shutdown_tx, mdns_shutdown_rx) = tokio::sync::oneshot::channel::<()>();
    
    let mdns_service = p2p::types::VmControlService {
        device_id: config.device_id.clone(),
        http_port: actual_port,          // axum 监听的实际端口
        vnc_port: None,                  // Phase 2 暂不广播，Phase 3 补充
        scrcpy_port: None,
        hostname: hostname::get()
            .map(|h| h.to_string_lossy().to_string())
            .unwrap_or_else(|_| "novaic-pc".to_string()),
        display_name: None,
    };

    tokio::spawn(async move {
        p2p::local_discovery::advertise(mdns_service, mdns_shutdown_rx).await;
    });

    // 关闭时同时停止 mDNS
    // shutdown 信号 → 先停 CloudBridge → 停 axum → 停 mDNS
    // ...
    let _ = mdns_shutdown_tx.send(());
}
```

---

## 九、移动端（Tauri Mobile）集成

### 前端 → Rust → mDNS 发现

```
React Native / Tauri Mobile 前端
  → invoke('start_discovery')
       ↓
  Tauri Mobile main.rs（P2P 命令）
  → 启动 p2p::local_discovery::discover()
  → 发现事件通过 Tauri emit 推送到前端
       ↓
  前端显示设备列表
  → 用户选择设备
  → invoke('connect_to_vmcontrol', { device_id, host, port })
```

### Tauri Mobile Commands

```rust
// mobile-app/src-tauri/src/p2p_commands.rs

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex, oneshot};
use tauri::{AppHandle, Emitter};
use p2p::{local_discovery, types::{DiscoveryEvent, VmControlService}};

type DiscoveredDevices = Arc<Mutex<HashMap<String, VmControlService>>>;
type DiscoveryShutdown = Arc<Mutex<Option<oneshot::Sender<()>>>>;

#[tauri::command]
pub async fn start_discovery(
    app: AppHandle,
    devices_state: tauri::State<'_, DiscoveredDevices>,
    shutdown_state: tauri::State<'_, DiscoveryShutdown>,
) -> Result<(), String> {
    // 如果已在发现中，先停止
    let mut shutdown_guard = shutdown_state.lock().await;
    if let Some(old_tx) = shutdown_guard.take() {
        let _ = old_tx.send(());
    }

    let (tx, mut rx) = mpsc::channel::<DiscoveryEvent>(32);
    let (shutdown_tx, shutdown_rx) = oneshot::channel();
    *shutdown_guard = Some(shutdown_tx);
    drop(shutdown_guard);

    let devices_clone = Arc::clone(&devices_state.inner());
    let app_clone = app.clone();

    // 发现事件处理
    tokio::spawn(async move {
        while let Some(event) = rx.recv().await {
            let mut devices = devices_clone.lock().await;
            match event {
                DiscoveryEvent::Discovered(service) => {
                    devices.insert(service.device_id.clone(), service.clone());
                    let _ = app_clone.emit("p2p://device-discovered", &service);
                }
                DiscoveryEvent::Removed(device_id) => {
                    devices.remove(&device_id);
                    let _ = app_clone.emit("p2p://device-removed", &device_id);
                }
            }
        }
    });

    // 启动 mDNS 发现
    tokio::spawn(async move {
        local_discovery::discover(tx, shutdown_rx).await;
    });

    Ok(())
}

#[tauri::command]
pub async fn stop_discovery(
    shutdown_state: tauri::State<'_, DiscoveryShutdown>,
) -> Result<(), String> {
    let mut guard = shutdown_state.lock().await;
    if let Some(tx) = guard.take() {
        let _ = tx.send(());
    }
    Ok(())
}

#[tauri::command]
pub async fn list_discovered_devices(
    devices_state: tauri::State<'_, DiscoveredDevices>,
) -> Result<Vec<VmControlService>, String> {
    let devices = devices_state.lock().await;
    Ok(devices.values().cloned().collect())
}
```

### 前端 React 使用

```typescript
// hooks/useDeviceDiscovery.ts
import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

interface VmControlService {
  device_id: string;
  http_port: number;
  hostname: string;
  display_name?: string;
  vnc_port?: number;
  scrcpy_port?: number;
}

export function useDeviceDiscovery() {
  const [devices, setDevices] = useState<Map<string, VmControlService>>(new Map());

  useEffect(() => {
    invoke('start_discovery').catch(console.error);

    const unlistenDiscovered = listen<VmControlService>('p2p://device-discovered', e => {
      setDevices(prev => new Map(prev).set(e.payload.device_id, e.payload));
    });

    const unlistenRemoved = listen<string>('p2p://device-removed', e => {
      setDevices(prev => {
        const next = new Map(prev);
        next.delete(e.payload);
        return next;
      });
    });

    return () => {
      invoke('stop_discovery').catch(console.error);
      unlistenDiscovered.then(f => f());
      unlistenRemoved.then(f => f());
    };
  }, []);

  return Array.from(devices.values());
}
```

---

## 十、LAN 直连会话建立

发现设备后，移动端直接通过 HTTP/WebSocket 连接 VmControl（不经过 Gateway）：

```
连接 VNC（noVNC）：
  ws://{hostname}:{vnc_port}/api/vnc/{vm_id}
  
连接 scrcpy：
  {hostname}:{scrcpy_port}  (原始 TCP)
  或
  ws://{hostname}:{scrcpy_port}/api/android/scrcpy/{device_id}
```

### 安全性（LAN 内）

LAN 直连**无 JWT 验证**（Phase 2 暂不实现），因为：
1. 局域网内可信度较高
2. 连接前通过 mDNS TXT 记录中的 device_id 确认设备身份
3. Phase 3 引入 TLS/Ed25519 后，LAN 直连也可以加上认证

> 如需立即加认证：VmControl 可在 TXT 记录中广播一个短期 session token，  
> 移动端拿 token 发起连接，VmControl 验证。

---

## 十一、平台注意事项

### macOS（PC VmControl）

- `mdns-sd` 纯 Rust 实现，无需系统权限，直接可用
- 防火墙可能拦截 mDNS 5353 端口，需要提示用户允许

### iOS（Tauri Mobile）

- 需要在 `Info.plist` 中声明：
  ```xml
  <key>NSBonjourServices</key>
  <array>
      <string>_novaic._tcp</string>
  </array>
  <key>NSLocalNetworkUsageDescription</key>
  <string>用于在局域网内发现 PC 上的 NovAIC 设备</string>
  ```
- iOS 14+ 会弹出"允许在局域网上查找设备"权限提示

### Android（Tauri Mobile）

- `mdns-sd` 的 Android 支持通过 JNI 调用 `android.net.nsd.NsdManager`（mdns-sd 0.11+ 支持）
- 需要 `ACCESS_WIFI_STATE` 和 `CHANGE_WIFI_MULTICAST_STATE` 权限

---

## 十二、连接优先级策略

Phase 2 完成后，连接策略如下（Phase 3 补充远程路径后完整）：

```
用户发起连接 device_id=X
  ↓
查询本地已发现设备
  ├── 找到 (device_id=X，LAN 可达)
  │     → 直接 LAN 连接（ws://{lan_ip}:{port}）
  │     → 延迟 < 2ms，最优
  └── 未找到 (不在 LAN 内)
        → （Phase 3）P2P QUIC 打洞
        → 延迟 20~100ms（取决于网络）
```

---

## 十三、完成标准

Phase 2 完成的判断标准：

1. ✅ `p2p` workspace crate 初始化，编译通过
2. ✅ PC 启动 VmControl 后，iOS/Android 上能自动发现该设备
3. ✅ 前端显示设备列表，设备下线后自动从列表移除
4. ✅ LAN 内直接通过 `ws://{lan_ip}:{port}` 建立 VNC 连接
5. ✅ iOS `Info.plist` 和 Android 权限配置正确
6. ⬜ LAN 直连不经过 Gateway（直连 VmControl HTTP/WS）
7. ⬜ 移动端发现到 PC 后显示设备名称和状态
