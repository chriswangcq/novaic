# my-devices API 文档（Phase 2）

> `GET /api/p2p/my-devices` — 列出当前用户所有已注册 P2P 设备（含离线）。

---

## 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `current_app_instance_id` | string | **推荐**。本机 app_instance_id。Gateway 通过 DeviceRegistry 查到对应 pc_client_id，在对应设备和楼层标注 `is_local`。 |
| `current_device_id` | string | 兼容旧版。直接传入本机 pc_client_id 时标注 is_local。若同时提供 `current_app_instance_id` 则忽略。 |

---

## 响应

```json
{
  "devices": [
    {
      "device_id": "...",
      "pc_client_id": "...",
      "ext_addr": "ip:port",
      "online": true,
      "last_seen": 1234567890,
      "is_local": true,
      "app_instance_id": "...",
      "machine_label": "..."
    }
  ],
  "by_app_instance": [
    {
      "app_instance_id": "...",
      "machine_label": "...",
      "is_local": true,
      "devices": [...]
    }
  ]
}
```

- `is_local`：仅当传入 `current_app_instance_id` 或 `current_device_id` 且匹配时存在。
- `pc_client_id`：与 `device_id` 同值（物理 PC 标识）。

---

## 调用方

| 调用方 | 传参 | 说明 |
|--------|------|------|
| `get_vnc_proxy_url` | `current_app_instance_id` | Rust 命令，从 AppInstanceState 读取 |
| `get_scrcpy_proxy_url` | `current_app_instance_id` | 同上 |
| `vnc_bridge_connect` | `current_app_instance_id` | 同上 |
| 前端 `gateway_get` | `current_app_instance_id` | 可选，从 useAppStore.appInstanceId 读取 |
