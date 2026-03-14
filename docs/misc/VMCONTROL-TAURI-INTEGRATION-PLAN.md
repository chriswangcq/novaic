# VmControl 与 Tauri App 集成方案

## 1. 当前架构分析

### 1.1 VmControl 现状

VmControl 是一个独立的 Rust HTTP 服务，提供：

| 功能模块 | 说明 |
|---------|------|
| **VM 管理** | QEMU VM 的注册、暂停、恢复、关机（通过 QMP） |
| **Guest Agent** | VM 内命令执行、文件读写 |
| **VNC 代理** | WebSocket ↔ Unix Socket 双向转发 |
| **Android 管理** | AVD 创建/删除、模拟器启动/停止 |
| **Scrcpy 代理** | Android 屏幕流 WebSocket 代理 |
| **Mobile Use API** | Android 设备的截图、触控、Shell、文件、UI 自动化 |
| **VMUSE 代理** | 转发请求到 VM 内的 VMUSE 服务 |

**技术栈**：
- HTTP Server: `axum 0.7`
- 异步运行时: `tokio`
- WebSocket: `axum::ws`
- 状态管理: `Arc<RwLock<HashMap<String, VmManager>>>`

### 1.2 Tauri App 现状

Tauri App 通过 `std::process::Command` 启动 VmControl 作为独立进程：

```rust
// main.rs 中的 VmControlProcess
struct VmControlProcess {
    process: Option<Child>,
    port: u16,
}

impl VmControlProcess {
    fn start(&mut self, app: &AppHandle) -> Result<(), String> {
        let vmcontrol_path = resolve_vmcontrol_binary_path(app)?;
        let child = Command::new(&vmcontrol_path)
            .arg("--port").arg("19996")
            .arg("--data-dir").arg(&data_dir_str)
            .spawn()?;
        self.process = Some(child);
    }
}
```

**问题**：
1. 需要单独编译和分发 VmControl 二进制
2. 进程间通过 HTTP 通信，增加延迟和复杂性
3. 进程生命周期管理复杂（orphan 进程问题）
4. 鉴权逻辑需要在两处实现

---

## 2. 集成目标

将 VmControl 从独立进程改为 Tauri App 的内嵌库，实现：

1. **单一二进制**：VmControl 功能编译进 Tauri App
2. **共享状态**：通过 Tauri State 管理 VM/Android 状态
3. **统一鉴权**：鉴权逻辑只在 Tauri 层实现一次
4. **简化部署**：无需单独分发 VmControl 二进制
5. **更好的生命周期管理**：App 退出时自动清理资源

---

## 3. 集成方案

### 3.1 方案选择

| 方案 | 优点 | 缺点 |
|------|------|------|
| **A. 完全内嵌** | 单一二进制、共享状态 | 改动大、HTTP API 需重写为 Tauri Commands |
| **B. 内嵌 HTTP Server** | 改动小、保持 HTTP API | 仍有进程内 HTTP 开销 |
| **C. 混合模式** | 渐进式迁移、风险低 | 架构复杂 |

**推荐：方案 B - 内嵌 HTTP Server**

理由：
1. VmControl 的 HTTP API 已被 Gateway 和 Tools Server 使用，保持兼容
2. WebSocket 端点（VNC、Scrcpy）需要 HTTP Server
3. 改动最小，风险最低
4. 未来可渐进式迁移到 Tauri Commands

### 3.2 实现步骤

#### Step 1: 修改 VmControl 为 Library

**修改 `vmcontrol/Cargo.toml`**：

```toml
[lib]
name = "vmcontrol"
path = "src/lib.rs"

[[bin]]
name = "vmcontrol"
path = "src/main.rs"
required-features = ["binary"]

[features]
default = []
binary = ["clap"]  # CLI 参数解析只在独立运行时需要

[dependencies]
clap = { version = "4", features = ["derive"], optional = true }
# ... 其他依赖保持不变
```

**修改 `vmcontrol/src/lib.rs`**：

```rust
pub mod error;
pub mod config;
pub mod qemu;
pub mod vnc;
pub mod scrcpy;
pub mod android;
pub mod api;

pub use error::{VmError, Result};
pub use config::Config;
pub use api::{ApiServer, routes::{AppState, AndroidState, CombinedState, create_router}};

// 新增：内嵌启动函数
pub async fn start_embedded_server(
    port: u16,
    host: &str,
    data_dir: Option<std::path::PathBuf>,
) -> anyhow::Result<()> {
    use std::net::SocketAddr;
    use std::collections::HashMap;
    use std::sync::Arc;
    use tokio::sync::RwLock;
    use tower_http::cors::CorsLayer;

    let state: AppState = Arc::new(RwLock::new(HashMap::new()));
    
    // 自动注册运行中的 VM
    crate::api::routes::vm::auto_register_running_vms(&state).await;
    
    // 预启动 scrcpy servers
    crate::scrcpy::pre_start_scrcpy_servers().await;
    
    let app = create_router(state, data_dir).layer(CorsLayer::permissive());
    let addr: SocketAddr = format!("{}:{}", host, port).parse()?;
    
    tracing::info!("vmcontrol embedded server starting on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    
    Ok(())
}
```

#### Step 2: 在 Tauri App 中添加 VmControl 依赖

**修改 `novaic-app/src-tauri/Cargo.toml`**：

```toml
[dependencies]
# ... 现有依赖

# VmControl 作为库依赖
vmcontrol = { path = "vmcontrol" }
```

#### Step 3: 修改 Tauri App 启动逻辑

**修改 `novaic-app/src-tauri/src/main.rs`**：

```rust
// 移除 VmControlProcess struct 和相关代码

// 新增：VmControl 状态管理
struct VmControlState {
    shutdown_tx: Option<tokio::sync::oneshot::Sender<()>>,
}

impl VmControlState {
    fn new() -> Self {
        Self { shutdown_tx: None }
    }
}

// 在 setup 中启动 VmControl
.setup(|app| {
    // ... 现有 setup 代码
    
    // 启动内嵌 VmControl server
    let data_dir = app.path().app_data_dir()?;
    let (shutdown_tx, shutdown_rx) = tokio::sync::oneshot::channel();
    
    tauri::async_runtime::spawn(async move {
        tokio::select! {
            result = vmcontrol::start_embedded_server(
                PORT_VMCONTROL,
                LOOPBACK_HOST,
                Some(data_dir),
            ) => {
                if let Err(e) = result {
                    eprintln!("[VmControl] Server error: {}", e);
                }
            }
            _ = shutdown_rx => {
                println!("[VmControl] Shutdown signal received");
            }
        }
    });
    
    // 存储 shutdown_tx 用于退出时关闭
    let vmcontrol_state = Arc::new(Mutex::new(VmControlState { 
        shutdown_tx: Some(shutdown_tx) 
    }));
    app.manage(vmcontrol_state);
    
    Ok(())
})

// 在 RunEvent::Exit 中关闭 VmControl
.run(|app, event| {
    if let tauri::RunEvent::Exit = event {
        // 发送关闭信号
        if let Some(state) = app.try_state::<Arc<Mutex<VmControlState>>>() {
            if let Ok(mut guard) = state.lock() {
                if let Some(tx) = guard.shutdown_tx.take() {
                    let _ = tx.send(());
                }
            }
        }
        
        // ... 其他清理代码
    }
})
```

#### Step 4: 清理旧代码

1. 删除 `resolve_vmcontrol_binary_path()` 函数
2. 删除 `VmControlProcess` struct 及其实现
3. 删除 Phase 1 中启动 VmControl 进程的代码
4. 更新 `RunEvent::Exit` 中的 VmControl 关闭逻辑

#### Step 5: 更新构建脚本

**修改 `novaic-app/src-tauri/tauri.conf.json`**：

```json
{
  "bundle": {
    "resources": [
      // 移除 vmcontrol 二进制
      // "vmcontrol/vmcontrol"  <- 删除这行
    ]
  }
}
```

---

## 4. 详细实现计划

### Phase 1: 准备工作

| 任务 | 文件 | 说明 |
|------|------|------|
| 1.1 | `vmcontrol/Cargo.toml` | 添加 lib/bin 配置和 features |
| 1.2 | `vmcontrol/src/lib.rs` | 添加 `start_embedded_server` 函数 |
| 1.3 | `vmcontrol/src/main.rs` | 添加 `#[cfg(feature = "binary")]` 条件编译 |

### Phase 2: Tauri 集成

| 任务 | 文件 | 说明 |
|------|------|------|
| 2.1 | `src-tauri/Cargo.toml` | 添加 vmcontrol 依赖 |
| 2.2 | `src-tauri/src/main.rs` | 实现内嵌启动逻辑 |
| 2.3 | `src-tauri/src/main.rs` | 实现优雅关闭逻辑 |

### Phase 3: 清理与测试

| 任务 | 文件 | 说明 |
|------|------|------|
| 3.1 | `src-tauri/src/main.rs` | 删除旧的 VmControlProcess 代码 |
| 3.2 | `tauri.conf.json` | 移除 vmcontrol 资源配置 |
| 3.3 | - | 端到端测试 |

---

## 5. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 依赖冲突 | 编译失败 | 统一依赖版本（tokio、serde 等） |
| 异步运行时冲突 | 运行时 panic | 确保使用同一个 tokio runtime |
| 内存占用增加 | 性能下降 | VmControl 本身内存占用小，影响可忽略 |
| WebSocket 兼容性 | VNC/Scrcpy 失效 | 保持 HTTP Server 架构，WebSocket 不变 |

---

## 6. 验证清单

- [ ] VmControl 可作为库编译
- [ ] Tauri App 可正常启动
- [ ] VmControl HTTP API 可访问（`http://127.0.0.1:19996/health`）
- [ ] VM 管理功能正常（注册、暂停、恢复、关机）
- [ ] Android 模拟器管理正常
- [ ] VNC WebSocket 连接正常
- [ ] Scrcpy WebSocket 连接正常
- [ ] App 退出时 VM 正常关闭
- [ ] App 退出时 Android 模拟器正常关闭

---

## 7. 后续优化（可选）

### 7.1 渐进式迁移到 Tauri Commands

对于不需要 HTTP 的内部调用，可以逐步迁移为 Tauri Commands：

```rust
#[tauri::command]
async fn vm_list(state: State<'_, VmState>) -> Result<Vec<VmInfo>, String> {
    // 直接调用 VmControl 内部函数，无需 HTTP
}
```

### 7.2 状态共享优化

```rust
// 将 VmControl 状态注入 Tauri State
app.manage(vmcontrol_state.clone());

// 在 Tauri Commands 中直接访问
#[tauri::command]
async fn get_vm_status(
    vm_state: State<'_, vmcontrol::AppState>,
    id: String,
) -> Result<VmStatus, String> {
    let vms = vm_state.read().await;
    // 直接访问状态，无需 HTTP
}
```

### 7.3 云端连接

集成完成后，可以在 Tauri App 中添加云端连接逻辑：

```rust
// 连接到云端 Gateway
async fn connect_to_cloud(cloud_gateway_url: &str, auth_token: &str) {
    // WebSocket 长连接
    // 接收云端指令，转发到本地 VmControl
}
```

---

## 8. 时间线

| 阶段 | 预计工作量 |
|------|-----------|
| Phase 1: 准备工作 | 1-2 小时 |
| Phase 2: Tauri 集成 | 2-3 小时 |
| Phase 3: 清理与测试 | 1-2 小时 |
| **总计** | **4-7 小时** |
