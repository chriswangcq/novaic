# 系统稳定性与连接管理

> 基于 2026-02-07 QMP 连接稳定性问题的诊断与修复经验总结

## 目录

1. [长连接 vs 按需连接](#1-长连接-vs-按需连接)
2. [连接稳定性问题诊断方法](#2-连接稳定性问题诊断方法)
3. [VNC 为什么比 QMP 稳定](#3-vnc-为什么比-qmp-稳定)
4. [状态同步与进程监控](#4-状态同步与进程监控)
5. [实战案例：QMP 按需连接重构](#5-实战案例qmp-按需连接重构)

---

## 1. 长连接 vs 按需连接

### 连接模式对比

| 特性 | 长连接 | 按需连接 |
|------|--------|---------|
| **连接方式** | 启动时建立，一直保持 | 每次请求时建立，用完关闭 |
| **状态管理** | 有状态（保存在内存） | 无状态（不保存连接） |
| **性能** | 高（无握手开销） | 略低（每次都要握手） |
| **稳定性** | 低（连接断开后失败） | 高（自动恢复） |
| **错误恢复** | 需要实现重连机制 | 自动恢复（下次重新连接） |
| **资源占用** | 一直占用连接 | 按需占用 |
| **并发性** | 需要锁（串行） | 天然并发（每个请求独立） |

### 何时使用长连接

**适用场景**：
- 连接建立成本高（TLS 握手、复杂认证）
- 请求非常频繁（每秒多次）
- 需要推送（WebSocket、SSE）
- 连接非常稳定（内部网络、本地）

**前提条件**：
- ✅ 必须实现健康检查
- ✅ 必须实现自动重连
- ✅ 必须有连接状态监控

### 何时使用按需连接

**适用场景**（推荐）：
- 连接建立成本低（Unix socket、本地连接）
- 请求不频繁（偶尔调用）
- 连接可能不稳定（进程重启、网络波动）
- 简单系统（避免复杂度）

**优势**：
- ✅ 无需实现重连逻辑
- ✅ 自动容错
- ✅ 代码简单
- ✅ 无状态管理负担

---

## 2. 连接稳定性问题诊断方法

### 问题表现

当看到以下错误时，可能是连接管理问题：
- `Broken pipe`
- `Connection refused`
- `Connection reset by peer`
- `No such file or directory` (Unix socket)

### 诊断步骤

#### 步骤 1：确认连接对象是否存在

```bash
# 检查进程是否运行
ps aux | grep <进程名>

# 检查 Unix socket 是否存在
ls -lh /path/to/socket.sock

# 测试连接可达性
timeout 2 nc -U /path/to/socket.sock < /dev/null
```

#### 步骤 2：分析连接管理方式

**查看代码**：
```rust
// 长连接模式（有状态）
pub struct Manager {
    connection: QmpClient,  // ❌ 保存在内存
}

// 按需连接模式（无状态）
pub struct Manager {
    socket_path: String,  // ✅ 只保存路径
}
```

#### 步骤 3：检查错误发生时机

**问题模式分析**：

| 错误时机 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 第一次调用就失败 | 对象未启动 | 检查启动顺序 |
| 运行一段时间后失败 | 连接超时/断开 | 实现重连或改按需 |
| 对象重启后失败 | 状态未同步 | 实现状态监控 |
| 随机失败 | 并发竞争 | 加锁或改按需 |

#### 步骤 4：对比稳定的实现

**关键问题**：为什么 X 服务稳定，Y 服务不稳定？

找出差异点：
- 连接模式（长连接 vs 按需）
- 错误处理（是否有重试）
- 状态管理（是否监控连接状态）
- 并发控制（是否有锁保护）

---

## 3. VNC 为什么比 QMP 稳定

### 实战案例

**问题**：用户反馈 VNC 连接很稳定，但 QMP 经常出现 "Broken pipe"。

**诊断过程**：

#### 分析 VNC 实现

```rust
// novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs
pub async fn vnc_websocket(...) {
    // 每次 WebSocket 请求都新建 Unix Socket 连接
    let vnc_stream = UnixStream::connect(&vnc_socket).await?;
    // 用完就关闭（Drop）
}
```

**特点**：
- ✅ 每次请求新建连接
- ✅ 无状态（不保存连接）
- ✅ 自动恢复（下次重新连接）
- ✅ 错误隔离（一个失败不影响其他）

#### 分析 QMP 实现（修复前）

```rust
// novaic-app/src-tauri/vmcontrol/src/qemu/manager.rs
pub struct VmManager {
    pub qmp: QmpClient,  // ❌ 长连接保存在内存
}

// 启动时建立连接
let qmp = QmpClient::connect(socket).await?;
let manager = VmManager { qmp };

// 所有命令都用这个连接
vm.qmp.execute("screendump", args).await?;  // ❌ 连接断开后失败
```

**问题**：
- ❌ 启动时建立，长期持有
- ❌ 连接断开后没有检测
- ❌ 没有重连机制
- ❌ 所有后续命令都失败

### 根本差异

| 对比项 | VNC | QMP（修复前） |
|--------|-----|--------------|
| 连接模式 | 按需新建 ✅ | 长连接 ❌ |
| 连接状态 | 无状态 ✅ | 有状态（内存）❌ |
| 错误恢复 | 自动恢复 ✅ | 无恢复 ❌ |
| QEMU 重启后 | 自动工作 ✅ | 彻底失败 ❌ |

### 修复方案

**借鉴 VNC 的无状态设计**：

```rust
// 修复后：只保存路径
pub struct VmManager {
    pub qmp_socket: String,  // ✅ 只保存路径
}

// 每次命令临时连接
impl VmManager {
    pub async fn create_qmp_client(&self) -> Result<QmpClient> {
        QmpClient::connect(&self.qmp_socket).await  // ✅ 按需连接
    }
}

// 使用时
let mut qmp = vm.create_qmp_client().await?;
qmp.execute("screendump", args).await?;
// 连接自动关闭（Drop）✅
```

---

## 4. 状态同步与进程监控

### 问题：VM 状态不同步

**实战案例**：
- Gateway 停止了 VM（kill QEMU 进程）
- vmcontrol 不知道，仍显示 "running"
- 前端调用 API 失败："Broken pipe"

### 状态不一致的根源

```
[Gateway]              [vmcontrol]
   ↓                      ↓
Kill QEMU               持有旧状态
   ↓                      ↓
VM 停止              ✗ 仍显示 running
   ↓                      ↓
Socket 消失          ✗ 仍尝试连接
   ↓                      ↓
                        Broken pipe
```

### 解决方案

#### 方案 A：进程监控（推荐）

定期检查 QEMU 进程和 socket 是否存在：

```rust
impl VmManager {
    pub fn is_alive(&self) -> bool {
        // 检查 socket 文件是否存在
        std::path::Path::new(&self.qmp_socket).exists()
    }
}

// 在 API 调用前检查
if !vm.is_alive() {
    return Err("VM is not running");
}
```

#### 方案 B：状态同步 API

Gateway 停止 VM 时通知 vmcontrol：

```rust
// vmcontrol 提供取消注册 API
DELETE /api/vms/{id}

// Gateway 停止 VM 后调用
await vmcontrol.unregister_vm(vm_id);
```

#### 方案 C：心跳检测

定期 ping QMP 检查连接：

```rust
// 每 30 秒检查一次
async fn health_check() {
    for vm in vms.values() {
        match vm.create_qmp_client().await {
            Ok(mut qmp) => {
                // 连接正常
                if qmp.execute("query-status", None).await.is_err() {
                    // 标记为不可用
                    vm.status = "unavailable";
                }
            }
            Err(_) => {
                // 连接失败，标记为停止
                vm.status = "stopped";
            }
        }
    }
}
```

### 推荐架构

**按需连接 + 简单健康检查**：

```rust
// 1. 使用按需连接（主要防御）
let mut qmp = vm.create_qmp_client().await?;

// 2. API 调用前检查 socket（快速失败）
if !vm.is_alive() {
    return Err("VM is not running");
}

// 3. 可选：定期清理失效的 VM（后台任务）
async fn cleanup_dead_vms() {
    vms.retain(|_, vm| vm.is_alive());
}
```

---

## 5. 实战案例：QMP 按需连接重构

### 问题描述

- 用户报告浏览器工具 500 错误
- 错误信息："Broken pipe"
- 场景：QEMU 重启或运行一段时间后

### 诊断过程

#### 1. 对比分析

```bash
# VNC 很稳定 ✅
curl http://localhost:8080/api/vnc/... 
# 总是成功

# QMP 不稳定 ❌
curl -X POST http://localhost:8080/api/vms/{id}/screenshot
# 有时 500: Broken pipe
```

**问题**：为什么 VNC 稳定，QMP 不稳定？

#### 2. 查看代码差异

**VNC**（无状态）：
```rust
// 每次都新建连接
let vnc_stream = UnixStream::connect(&vnc_socket).await?;
```

**QMP**（有状态）：
```rust
// 启动时建立，一直持有
pub struct VmManager {
    pub qmp: QmpClient,  // ❌ 长连接
}
```

**结论**：QMP 使用长连接，VNC 使用按需连接。

#### 3. 确定修复方案

**方案对比**：

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 健康检查 + 重连 | 保持性能 | 复杂，难维护 | ❌ |
| 按需连接（像 VNC）| 简单，自动恢复 | 每次连接开销 | ✅ |

**决策**：采用按需连接，因为：
- QMP 命令不频繁（偶尔截图、暂停）
- Unix socket 连接开销小（< 1ms）
- 代码简单，无需维护状态

### 修复实施

#### 步骤 1：修改 VmManager 结构

```rust
// 修改前
pub struct VmManager {
    pub id: String,
    pub name: String,
    pub qmp: QmpClient,  // ❌ 保存连接
}

// 修改后
pub struct VmManager {
    pub id: String,
    pub name: String,
    pub qmp_socket: String,  // ✅ 只保存路径
}

// 添加辅助方法
impl VmManager {
    pub async fn create_qmp_client(&self) -> Result<QmpClient, VmError> {
        QmpClient::connect(&self.qmp_socket).await
    }
}
```

#### 步骤 2：更新所有调用点

```rust
// 修改前（5 个文件，约 20 处）
vm.qmp.execute("stop", None).await?;

// 修改后
let mut qmp = vm.create_qmp_client().await?;
qmp.execute("stop", None).await?;
// 连接自动关闭（Drop）
```

涉及文件：
- `vm.rs`: `pause_vm`, `resume_vm`, `shutdown_vm`
- `screen.rs`: `screenshot`
- `input.rs`: `keyboard_input`, `mouse_input`
- `main.rs`: `auto_register_running_vms`

#### 步骤 3：修改 VM 注册逻辑

```rust
// 修改前
pub async fn register_vm(...) -> Result<...> {
    let qmp = QmpClient::connect(&request.qmp_socket).await?;  // ❌ 建立连接
    let vm_manager = VmManager { qmp, ... };  // ❌ 保存连接
    state.insert(request.id, vm_manager);
}

// 修改后
pub async fn register_vm(...) -> Result<...> {
    // 只验证 socket 存在，不建立连接 ✅
    if !Path::new(&request.qmp_socket).exists() {
        return Err("QMP socket not found");
    }
    let vm_manager = VmManager {
        qmp_socket: request.qmp_socket,  // ✅ 只保存路径
        ...
    };
    state.insert(request.id, vm_manager);
}
```

#### 步骤 4：优化锁使用

```rust
// 修改前：需要 write lock（串行）
let mut vms = state.write().await;  // ❌ 互斥锁
let vm = vms.get_mut(&id)?;
vm.qmp.execute("stop", None).await?;

// 修改后：只需 read lock（并发）
let vms = state.read().await;  // ✅ 共享锁
let vm = vms.get(&id)?;
let mut qmp = vm.create_qmp_client().await?;  // ✅ 每个请求独立连接
qmp.execute("stop", None).await?;
```

### 修复效果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 稳定性 | ❌ Broken pipe | ✅ 自动恢复 |
| QEMU 重启后 | ❌ 彻底失败 | ✅ 自动工作 |
| 并发性 | ❌ write lock（串行）| ✅ read lock（并发）|
| 代码复杂度 | 高（状态管理）| 低（无状态）|
| 性能影响 | 无连接开销 | 每次 < 1ms（可忽略）|

### 关键收获

1. **简单胜过复杂**：按需连接比长连接 + 重连机制简单得多
2. **学习成功案例**：VNC 的稳定性给了我们答案
3. **性能不是首要**：1ms 的连接开销对于偶尔的命令可忽略
4. **无状态是美德**：无状态设计天然容错

---

## 总结：连接管理最佳实践

### 默认选择按需连接

除非有充分理由，否则使用按需连接：

✅ **按需连接的优势**：
- 自动容错
- 无状态
- 代码简单
- 天然并发

❌ **长连接的成本**：
- 需要健康检查
- 需要重连机制
- 状态管理复杂
- 并发需要加锁

### 何时才用长连接

**必要条件（全部满足）**：
1. 连接建立成本 > 10ms
2. 请求频率 > 每秒多次
3. 有完善的监控和重连机制
4. 连接非常稳定

### 关键原则

1. **对比学习**：找出稳定的实现，分析差异
2. **简单优先**：能用简单方案就不用复杂方案
3. **实测性能**：不要臆测性能问题，先实测
4. **无状态美德**：无状态设计自动容错

---

*最后更新：2026-02-07*
*案例：QMP 按需连接重构*
