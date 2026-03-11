# 服务并行启动方案

> 目标：所有 service 先同时启动，健康检查全部 OK 后再启动 Workers

---

## 一、当前启动流程（串行）

```
1. RO start
2. 等 RO health (最多 30s，先 sleep 1s 再检查)
3. Gateway start
4. VmControl start
5. Queue start
6. File start
7. TRS start
8. 等 TRS health (最多 30s)
9. Tools Server start
10. 等 Gateway health (最多 90s)
11. 等 Tools Server health (最多 45s)
12. 等 Queue health (最多 15s)
13. Workers start
```

**问题**：
- 完全串行，总耗时 = 各阶段之和
- 健康检查先 sleep 1s 再请求，即使服务 100ms 就绪也要多等 1s
- RO、TRS、Queue、File、VmControl 之间无依赖，本可并行

---

## 二、依赖关系

| 服务 | 启动依赖 | 说明 |
|------|----------|------|
| RO | 无 | |
| Gateway | 无 | 当前 lifespan 有 `check_runtime_orchestrator_health()` 是历史遗留，可移除；Gateway 的 RO 调用均由 Worker 触发 |
| TRS | 无 | |
| Queue | 无 | |
| File | 无 | |
| VmControl | 无 | |
| Tools Server | Gateway（弱）、TRS（弱） | `restore_from_gateway` 有 5 次重试；TRS 为运行时依赖 |
| Workers | Gateway、Queue、RO、Tools Server、TRS | 全部必须就绪 |

**结论**：所有服务均可并行启动，无启动顺序依赖。

---

## 三、方案对比

### 方案：全部并行 spawn + 统一健康检查（推荐）

**思路**：所有服务一次性 spawn，健康检查改为「先请求再 sleep」，并支持并发等待。

**前提**：移除 Gateway lifespan 中的 `check_runtime_orchestrator_health()`（Gateway 的 RO 调用均由 Worker 触发，启动阶段无需 RO）。

**Phase 1 - 一次性 spawn 所有服务**：
```
spawn: RO, Gateway, TRS, Queue, File, VmControl, Tools Server
```

**Phase 2 - 并发健康检查**：
```rust
// 伪代码
let checks = [
    ("RO", ro_health_url),
    ("Gateway", gw_health_url),
    ("TRS", trs_health_url),
    ("Tools Server", ts_health_url),
    ("Queue", qs_health_url),
];
// 每个检查：先请求，失败则 sleep 200-300ms 再试，直到超时
let results = join_all(checks.map(|(name, url)| check_until_ready(name, url, timeout))).await;
if results.all(ok) { start_workers(); }
```

**Phase 3 - 启动 Workers**

**健康检查优化**（与 BACKEND_STARTUP_SLOWNESS_ANALYSIS 一致）：
- 先发请求，再 sleep（避免固定多等 1s）
- 间隔从 1s 改为 200–300ms
- 并发检查，总耗时 ≈ 最慢服务的就绪时间

---

## 四、改动清单

| 位置 | 改动 |
|------|------|
| `main_gateway.py` | 移除 lifespan 中的 `check_runtime_orchestrator_health()` |
| `gateway_api.py` | 同上（split 验证用） |
| `main.rs` | Phase 1：一次性 spawn 所有 7 个服务 |
| `main.rs` | Phase 2：并发健康检查（先请求再 sleep，间隔 200–300ms） |
| `main.rs` | Phase 3：全部 OK 后启动 Workers |

## 五、main.rs 并行 spawn 伪代码

```rust
// Phase 1: Spawn all services in parallel
let ro_handle = tokio::spawn(async { runtime_orchestrator.start(...).await });
let gw_handle = tokio::spawn(async { gateway.start(...).await });
let trs_handle = tokio::spawn(async { tool_result_service.start(...).await });
// ... Queue, File, VmControl, Tools Server
// (实际用 lock + 顺序 spawn 也可，关键是进程都起来)

// 或简化：顺序 spawn 但不等待，全部 spawn 完再统一 health check
// 因为 spawn 本身很快，主要耗时在进程启动和健康检查

// Phase 2: Concurrent health checks (先请求再 sleep)
async fn wait_until_ready(name: &str, url: &str, timeout_secs: u64) -> bool {
    let client = reqwest::Client::new();
    for i in 0..(timeout_secs * 4) {  // 250ms 间隔
        if client.get(url).send().await.map(|r| r.status().is_success()).unwrap_or(false) {
            return true;
        }
        if i < timeout_secs * 4 - 1 {
            tokio::time::sleep(Duration::from_millis(250)).await;
        }
    }
    false
}

let (ro_ok, gw_ok, trs_ok, ts_ok, qs_ok) = tokio::join!(
    wait_until_ready("RO", &ro_url, 30),
    wait_until_ready("Gateway", &gw_url, 90),
    wait_until_ready("TRS", &trs_url, 30),
    wait_until_ready("Tools Server", &ts_url, 45),
    wait_until_ready("Queue", &qs_url, 15),
);

if ro_ok && gw_ok && trs_ok && ts_ok && qs_ok {
    // Phase 3: Start Workers
}
```

---

## 六、预期收益

| 场景 | 当前 | 优化后 |
|------|------|--------|
| 理想（各服务 0.5s 内就绪） | 串行 + 5×1s 固定延迟 ≈ 8–10s | 并行 + 0.25s 间隔 ≈ 1–2s |
| 一般（Gateway 5s、Tools 10s） | 各阶段累加 ≈ 30s+ | 取 max(Gateway, Tools, ...) ≈ 10–15s |

---

## 七、风险与回退

| 风险 | 缓解 |
|------|------|
| 某服务启动失败拖慢整体 | 各服务独立超时，失败可快速失败并中止 |
| 并发 spawn 导致资源争抢 | spawn 本身开销小，可观察；必要时可保留少量顺序 |
| RO 并行启动时较慢 | RO 超时从 30s 增至 60s；健康检查前加 500ms 初始延迟 |

**回退**：若并行启动带来问题，可回退到原串行顺序。

---

## 八、实际运行问题（2025-03）

**现象**：启动慢，发消息无反应

**根因**：
- RO 健康检查 30s 超时，并行启动时 RO（init_database + migration）较慢
- 超时后启动流程中止，**Workers 未启动**
- 消息存入 Gateway，但 Watchdog 未运行，无法处理

**修复**：
- RO 健康检查超时 30s → 60s
- 健康检查前增加 500ms 初始延迟
