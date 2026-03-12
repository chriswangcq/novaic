# Phase 2.3 多 PC 路由 — 详细方案

> P2-7、P2-8 实现方案与依赖关系。

---

## 问题

- `get_pc_client_manager(user_id)` 始终返回该用户第一台已连接 PC
- devices API（start/stop/status/setup）转发到该 PC，多 PC 场景无法指定目标

## 方案概览

1. **get_pc_client_manager** 支持可选 `pc_client_id`，指定时返回该 PC 的 adapter
2. **devices 表** 新增 `pc_client_id` 列，setup 时记录目标 PC
3. **devices API** 支持可选 `pc_client_id` 参数，优先级：显式传入 > device.pc_client_id > 第一个
4. **前端** 从 device 记录或 VncTarget 传入 pc_client_id

---

## 实现步骤

### P2-7: get_pc_client_manager

| 步骤 | 说明 |
|------|------|
| 7a | 签名改为 `get_pc_client_manager(user_id=None, pc_client_id=None)` |
| 7b | 当 pc_client_id 非空：若该 device 存在且属于 user_id，返回其 adapter；否则 _DisconnectedAdapter |
| 7c | 当 pc_client_id 为空：保持当前行为（第一个） |
| 7d | _DeviceManagerAdapter 增加 `pc_client_id` 属性，供 setup 后存储 |

### P2-8: devices API

| 步骤 | 说明 |
|------|------|
| 8a | Migration v54：`ALTER TABLE devices ADD COLUMN pc_client_id TEXT` |
| 8b | DeviceConfig 增加 `pc_client_id: Optional[str] = None` |
| 8c | DeviceRepository：create/update/get/_row_to_device 支持 pc_client_id |
| 8d | setup 完成后：`repo.update(device.id, pc_client_id=mgr.pc_client_id)` |
| 8e | start/stop/status/setup/vmuse 等：增加 `pc_client_id: str = Query(None)` |
| 8f | 解析逻辑：`target = pc_client_id or getattr(device, 'pc_client_id', None)`，传 `target` 给 get_pc_client_manager |
| 8g | DeviceResponse 增加 pc_client_id 字段，list/get 返回 |
| 8h | 前端 api.devices.start/stop/status 支持 pc_client_id 参数 |

---

## 调用链

```
前端: api.devices.start(deviceId, { pc_client_id?: string })
  → Gateway: POST /api/devices/{id}/start?pc_client_id=xxx
  → get_pc_client_manager(user_id, pc_client_id or device.pc_client_id)
  → forward_to_device(device_state)
```

---

## 兼容性

- 旧设备无 pc_client_id：fallback 到第一个 PC
- 前端不传 pc_client_id：使用 device.pc_client_id 或第一个
- 多 PC 且 device 未绑定：需显式传入，否则可能路由到错误 PC
