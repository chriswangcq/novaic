# vm_status_report 上报 stopped 设备实现方案

> 问题：App 刚启动时设备多为 stopped，当前只上报 running/connected，导致 pc_client_id 一直为 NULL，设备显示「未分配」。

---

## 1. 现状分析

### 1.1 当前逻辑

| 类型 | 数据源 | 过滤条件 | 结果 |
|------|--------|----------|------|
| Linux VM | `GET /api/vms` | 仅返回有 QMP socket 的 VM | **只含 running**（stopped 无 socket） |
| Android | `GET /api/android/devices` | cloud_bridge 只取 `status=connected/device` | **只含 connected** |

### 1.2 根因

- **Linux**：`list_vms` 通过 `discover_running_vms()` 扫描 `/tmp/novaic/novaic-qmp-*.sock`，stopped 的 VM 已删除 socket，无法发现。
- **Android**：`list_devices` 来自 `adb devices`，stopped 的模拟器**不在 adb 列表中**；cloud_bridge 又过滤了非 connected 的。

### 1.3 数据来源

要上报「本机管理的所有设备」（含 stopped），需要：

| 类型 | 全量列表来源 | 说明 |
|------|--------------|------|
| Linux VM | `data_dir/agents/<agent_id>/` 子目录 | 每个 setup 过的 VM 有目录，agent_id 即 device.id |
| Android AVD | `GET /api/android/avds` | 列出所有 AVD 名称，Gateway 用 avd_name 匹配 |
| Android 物理机 | `adb devices` 全部 | 含 offline，用 device_serial 匹配 |

---

## 2. 实现方案

### 2.1 方案 A：CloudBridge 扩展（推荐）

**改动点**：`cloud_bridge.rs` 的 `fetch_running_device_ids` 改为 `fetch_managed_device_ids`，上报三类数据：

- `vm_ids`：Linux 全量（running + stopped）
- `android_serials`：Android 已连接设备（保持现有逻辑）
- `android_avd_names`：**新增**，所有 AVD 名称（含 stopped）

**Linux 全量来源**：需要 VmControl 新增 API 或本地枚举。

**选项 A1**：VmControl 新增 `GET /api/vms/managed` — 枚举 `data_dir/agents/*` 返回所有 agent_id。
**选项 A2**：CloudBridge 直接读本地 `data_dir/agents/` 目录（需传入 data_dir 路径）。

**Gateway 处理**：`pc_client.py` 的 vm_status_report 逻辑扩展：

- `vm_ids`：按 device.id 更新 pc_client_id（已有）
- `android_serials`：按 device.device_serial 更新（已有）
- `android_avd_names`：**新增**，按 device.avd_name 匹配 Android 设备并更新 pc_client_id

### 2.2 方案 B：仅扩展 Android（最小改动）

- Linux：暂不改（需 VmControl 或 data_dir 支持）。
- Android：cloud_bridge 同时调用 `/api/android/avds`，取 `avd_names` 加入 vm_status_report；Gateway 新增按 avd_name 的 pc_client_id 更新。

---

## 3. 推荐实现步骤（方案 A）

### 3.1 VmControl：新增 managed VM 列表

**方式 1**：在 `vm.rs` 中新增 `GET /api/vms/managed`，枚举 `data_dir/agents/*` 目录名：

```rust
// 需要 data_dir 从环境或 state 传入
fn list_managed_vms(data_dir: &Path) -> Vec<String> {
    let agents_dir = data_dir.join("agents");
    if !agents_dir.exists() { return vec![]; }
    std::fs::read_dir(agents_dir)
        .ok()
        .into_iter()
        .flatten()
        .filter_map(|e| e.path().file_name()?.to_str().map(String::from))
        .filter(|s| !s.is_empty())
        .collect()
}
```

**方式 2**：`list_vms` 返回 running，新增 `list_managed` 合并 `discover_running_vms` + 目录枚举。或直接修改 `list_vms` 在返回中增加 stopped 的 id（需区分 status）。

**建议**：新增 `GET /api/vms/managed-ids`，返回 `Vec<String>`，仅 id 列表，用于 vm_status_report。

### 3.2 CloudBridge：`fetch_managed_device_ids`

```rust
async fn fetch_managed_device_ids(...) -> Result<(Vec<String>, Vec<String>, Vec<String>), ...> {
    let mut vm_ids = Vec::new();
    let mut android_serials = Vec::new();
    let mut android_avd_names = Vec::new();

    // 1. Linux: 优先 GET /api/vms/managed-ids，fallback 到 /api/vms
    let managed_url = format!("{}/api/vms/managed-ids", base);
    if let Ok(resp) = client.get(&managed_url).send().await {
        if resp.status().is_success() {
            if let Ok(ids) = resp.json::<Vec<String>>().await {
                vm_ids = ids;
            }
        }
    }
    if vm_ids.is_empty() {
        // fallback: 仅 running
        let vms = fetch_vms_from_list_api(&format!("{}/api/vms", base), client).await;
        vm_ids = vms;
    }

    // 2. Android devices: 全部（去掉 connected 过滤），或保留 connected 用于 serial 映射
    let devices = fetch_android_devices(&format!("{}/api/android/devices", base), client).await;
    for d in devices {
        if let Some(serial) = d.get("serial").and_then(|v| v.as_str()) {
            if !serial.is_empty() {
                android_serials.push(serial.to_string());
            }
        }
    }

    // 3. Android AVDs: 新增
    let avds = fetch_android_avds(&format!("{}/api/android/avds", base), client).await;
    for a in avds {
        if let Some(name) = a.get("name").and_then(|v| v.as_str()) {
            if !name.is_empty() {
                android_avd_names.push(name.to_string());
            }
        }
    }

    Ok((vm_ids, android_serials, android_avd_names))
}
```

vm_status_report 负载：

```json
{
  "type": "vm_status_report",
  "vm_ids": ["agent-id-1", "agent-id-2"],
  "android_serials": ["emulator-5554"],
  "android_avd_names": ["Pixel_API_34", "novaic_xxx"]
}
```

### 3.3 Gateway：pc_client.py 扩展

```python
# vm_status_report 分支
vm_ids = set(data.get("vm_ids", []))
android_serials = set(data.get("android_serials", []))
android_avd_names = set(data.get("android_avd_names", []))  # 新增

for vid in vm_ids:
    ...
for serial in android_serials:
    ...
for avd_name in android_avd_names:
    if avd_name:
        rows = db.fetchall(
            "SELECT id FROM devices WHERE user_id = ? AND type = 'android' AND avd_name = ?",
            (user_id, avd_name),
        )
        for row in rows:
            repo.update(row["id"], pc_client_id=pc_id)
```

---

## 4. 最小可行方案（先解决 Android）

若 Linux 的 `managed-ids` 需要更多重构，可先做 Android：

1. **cloud_bridge.rs**：增加对 `/api/android/avds` 的调用，将 `android_avd_names` 加入 vm_status_report。
2. **pc_client.py**：增加对 `android_avd_names` 的处理，按 `avd_name` 更新 device 的 `pc_client_id`。

这样至少 Android 的 stopped AVD 能在首次上报时正确分配到 PC。

---

## 5. Linux 的 data_dir 来源

VmControl 的 data_dir 来源：

- 环境变量 `NOVAIC_DATA_DIR`
- 或默认：`~/Library/Application Support/com.novaic.app`（macOS）

CloudBridge 与 VmControl 同进程，可通过环境变量或 VmControl 的 Config 获取。新增 managed-ids API 时，state 需包含 data_dir。
