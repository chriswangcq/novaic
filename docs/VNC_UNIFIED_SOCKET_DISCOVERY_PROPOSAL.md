# VNC 后端 Socket 与发现统一方案

> **已实施**：B+C 方案（2026-03-12）

## 一、现状

| 类型 | Socket 路径 | 发现方式 |
|------|-------------|----------|
| **maindesk** | `/tmp/novaic/novaic-vnc-{vm_id}.sock` | 直接查找，存在即用 |
| **subuser** | `/tmp/novaic/vnc-{vm_id}-{username}.sock` | 轮询 port 文件 30s → 建 Unix→TCP 代理 |

差异：
1. **路径格式**：maindesk 用 `novaic-vnc-*`，subuser 用 `vnc-*`（`:` 替换为 `-`）
2. **发现**：maindesk 一次查找，subuser 轮询 + 代理创建

---

## 二、统一目标

1. **统一路径**：`/tmp/novaic/vnc-{safe_resource_id}.sock`
   - maindesk: `vnc-{vm_id}.sock`
   - subuser: `vnc-{vm_id}-{username}.sock`（已有）

2. **统一发现**：单一 `ensure_vnc_endpoint(resource_id)` 入口，内部按 resource_id 分支，对外无感知

---

## 三、方案对比

### 方案 A：仅 vnc_endpoint 统一（最小改动）

**思路**：不改 vm.rs，vnc_endpoint 内统一路径与发现逻辑。

| 改动点 | 内容 |
|--------|------|
| **maindesk 路径** | 优先查 `vnc-{vm_id}.sock`，不存在则查 `novaic-vnc-{vm_id}.sock`；若在 legacy 路径找到，创建 `vnc-{vm_id}.sock` 指向它的符号链接，并返回统一路径 |
| **maindesk 发现** | 可选：从「一次查找」改为「短轮询」（如 3 次 × 200ms），与 subuser 的「轮询」语义统一 |
| **subuser** | 保持不变，已用 `vnc-{vm_id}-{username}.sock` |

**优点**：不改 agent 启动逻辑，兼容现有 QEMU 配置  
**缺点**：maindesk 首次需建 symlink，依赖 legacy 路径

---

### 方案 B：Agent 运行时统一路径（推荐）

**思路**：vm.rs 启动 VM 时使用统一路径 `vnc-{vm_id}.sock`。

| 改动点 | 内容 |
|--------|------|
| **vm.rs** | `vnc_socket` 从 `novaic-vnc-{id}.sock` 改为 `vnc-{id}.sock` |
| **stop_vm** | 删除 `vnc-{id}.sock`（不再删除 novaic-vnc-*） |
| **is_vnc_socket_live** | 检查 `vnc-{id}.sock` |
| **vnc_endpoint** | maindesk 只查 `vnc-{vm_id}.sock`，找不到再 fallback 到 `novaic-vnc-{vm_id}.sock`（兼容旧 VM） |

**优点**：路径完全统一，无需 symlink  
**缺点**：需改 vm.rs，已有 VM 需重启后才用新路径

---

### 方案 C：统一发现接口（发现逻辑统一）

**思路**：路径可暂不统一，先统一「发现」的调用方式与语义。

| 改动点 | 内容 |
|--------|------|
| **ensure_vnc_endpoint** | 重构为单一入口，内部按 `resource_id.contains(':')` 分支，对外只返回 `PathBuf` |
| **maindesk** | 轮询 `vnc-{vm_id}.sock` 或 `novaic-vnc-{vm_id}.sock` 存在（如 3 次 × 200ms），与 subuser 的轮询语义一致 |
| **subuser** | 保持现有轮询 port 文件 + 代理逻辑 |

**优点**：发现流程统一，便于后续扩展  
**缺点**：maindesk 增加轮询，可能略增延迟（通常 < 600ms）

---

## 四、推荐组合：B + C

1. **方案 B**：vm.rs 使用 `vnc-{vm_id}.sock`，实现路径统一  
2. **方案 C**：ensure_vnc_endpoint 统一发现接口，maindesk 也采用短轮询

### 4.1 vm.rs 改动

```rust
// 原
let vnc_socket = format!("/tmp/novaic/novaic-vnc-{}.sock", agent_id);

// 改
let vnc_socket = format!("/tmp/novaic/vnc-{}.sock", agent_id);
```

同时更新：`stop_vm`、`is_vnc_socket_live` 中的路径。

### 4.2 vnc_endpoint.rs 改动

```rust
// 统一路径格式
fn unified_socket_path(resource_id: &str) -> PathBuf {
    let safe = resource_id.replace(':', "-");
    PathBuf::from(NOVAIC_DIR).join(format!("vnc-{}.sock", safe))
}

// maindesk: 轮询 vnc-{vm_id}.sock，fallback novaic-vnc-{vm_id}.sock
// subuser: 保持现有逻辑（已用 vnc-{vm_id}-{username}.sock）
```

### 4.3 发现统一

- maindesk：轮询 3 次 × 200ms，先查 `vnc-{vm_id}.sock`，再查 `novaic-vnc-{vm_id}.sock`
- subuser：保持 30s 轮询 port 文件 + 代理创建

---

## 五、实施步骤

| 阶段 | 内容 |
|------|------|
| **1** | 修改 vm.rs：vnc_socket 改为 `vnc-{id}.sock` |
| **2** | 修改 vnc_endpoint maindesk 分支：只查 `vnc-{vm_id}.sock`，保留 `novaic-vnc-*` fallback |
| **3** | （可选）maindesk 改为短轮询，与 subuser 发现语义统一 |
| **4** | 清理：移除 novaic-vnc fallback（待旧 VM 全部迁移后） |

---

## 六、兼容性

- **新启动 VM**：直接使用 `vnc-{id}.sock`
- **已运行 VM**：仍用 `novaic-vnc-{id}.sock`，通过 fallback 继续可用
- **subuser**：已用 `vnc-{vm_id}-{username}.sock`，无需改动
