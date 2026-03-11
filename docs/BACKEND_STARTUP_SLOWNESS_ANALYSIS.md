# 后端启动慢问题分析

> 基于 `novaic-app/src-tauri/src/main.rs` 与 `vmcontrol/src/main.rs` 分析

---

## 一、主要瓶颈

### 1. 健康检查轮询：先 sleep 再检查（最严重）

**位置**：main.rs 第 1816–1826、1922–1932、1966–1977、1994–2005、2021–2032 行

**问题**：每个健康检查循环都是**先 sleep(1s) 再发请求**：

```rust
for i in 0..RO_HEALTH_TIMEOUT_SECS {
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;  // 先等 1 秒
    match client.get(&ro_health_url).send().await {
        Ok(resp) if resp.status().is_success() => { break; }
        _ => {}
    }
}
```

**影响**：即使服务 100ms 内就绪，也要至少等 1 秒。5 个健康检查（RO、TRS、Gateway、Tools Server、Queue Service）在理想情况下也会多出 **5 秒**。

---

### 2. 完全串行启动

**启动顺序**（必须等前一个就绪才能继续）：

1. Runtime Orchestrator → 等 RO 就绪（最多 30s）
2. Gateway → 等 Gateway 就绪（最多 90s）
3. VmControl
4. Queue Service
5. File Service
6. Tool Result Service → 等 TRS 就绪（最多 30s）
7. Tools Server → 等 Tools Server 就绪（最多 45s）
8. Queue Service 健康检查（最多 15s）
9. Workers

**可并行部分**：Queue Service、File Service、Tool Result Service 之间无依赖，可在 RO 就绪后**同时启动**，当前却是串行。

---

### 3. VmControl 启动阻塞

**位置**：`vmcontrol/src/main.rs` 第 50–54 行

```rust
auto_register_running_vms(state.clone()).await;
pre_start_scrcpy_servers().await;  // 最多等 30 秒
```

**问题**：
- `pre_start_scrcpy_servers()` 会 `list_all_devices()`（调用 adb），可能较慢
- 对每个已连接 Android 设备执行 `ensure_scrcpy_server()`，超时 30 秒
- 无设备时较快，有设备时可能明显拖慢启动

---

### 4. Zombie 清理

**位置**：main.rs 第 1777 行、1292 行

- `kill_zombie_processes()` 会 `pkill -9 -f` 多个模式
- 若有进程被 kill，会 `sleep(PROCESS_TERM_WAIT_MS)` = 500ms
- 正常情况下无僵尸进程，影响较小

---

### 5. Gateway 启动本身可能较慢

**注释**（第 1959 行）："Gateway startup can include migrations and warm-up work in production bundles"

- 首次启动可能做 DB migration
- 超时设为 90s，说明预期可能较慢

---

## 二、优化建议（按优先级）

| 优先级 | 改动 | 预期收益 |
|--------|------|----------|
| **P0** | 健康检查改为**先请求再 sleep** | 理想情况可减少约 5s |
| **P1** | 健康检查间隔从 1s 改为 200–300ms | 进一步缩短等待 |
| **P2** | Queue/File/TRS 在 RO 就绪后并行启动 | 减少约 2–3s |
| **P3** | VmControl 的 `pre_start_scrcpy_servers` 改为后台执行 | 不阻塞主流程 |
| **P4** | Gateway 首次 migration 优化或预执行 | 视 migration 耗时而定 |

---

## 三、P0 修改示例（健康检查先检查再 sleep）

**当前逻辑**：
```rust
for i in 0..RO_HEALTH_TIMEOUT_SECS {
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    if client.get(&url).send().await?.status().is_success() { break; }
}
```

**建议逻辑**：
```rust
for i in 0..RO_HEALTH_TIMEOUT_SECS {
    if client.get(&url).send().await?.status().is_success() {
        println!("[Services] Runtime Orchestrator is ready after {}s", i);
        ro_ready = true;
        break;
    }
    if i < RO_HEALTH_TIMEOUT_SECS - 1 {
        tokio::time::sleep(tokio::time::Duration::from_millis(300)).await;
    }
}
```

---

## 四、时间线估算（当前 vs 优化后）

| 阶段 | 当前（理想） | 优化后（理想） |
|------|--------------|----------------|
| Zombie 清理 | 0–0.5s | 0–0.5s |
| RO 启动 + 健康检查 | 1s + 启动时间 | 0.3s + 启动时间 |
| Gateway 启动 + 健康检查 | 1s + 启动时间 | 0.3s + 启动时间 |
| TRS 启动 + 健康检查 | 1s + 启动时间 | 0.3s + 启动时间 |
| Tools Server 健康检查 | 1s + 启动时间 | 0.3s + 启动时间 |
| Queue Service 健康检查 | 1s + 启动时间 | 0.3s + 启动时间 |
| **仅健康检查固定延迟** | **~5s** | **~0.5s** |

---

## 五、相关代码位置

- 健康检查循环：main.rs 1816、1922、1966、1994、2021 行
- 启动顺序：main.rs 1794–2060 行
- VmControl 预启动：vmcontrol/src/main.rs 50–54、154–204 行
- 配置常量：config.rs `PROCESS_TERM_WAIT_MS`、`SERVICE_WAIT_TIMEOUT_SECS` 等
