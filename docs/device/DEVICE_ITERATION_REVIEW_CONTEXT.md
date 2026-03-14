# Device / pc_client 迭代 Code Review 上下文

## 迭代范围

基于 `docs/DEVICE_PC_CLIENT_ONLINE_PLAN.md` 的完整实现：
- Phase 1: vm_status_report 只写不清
- Phase 2: 前端 available 推导 + UI unavailable
- Phase 3: ensure_device_available 校验
- Phase 4: API available 字段 + Android vm_status_report

## 关键改动文件

| 区域 | 文件 | 改动要点 |
|------|------|----------|
| 前端 | AgentDrawer.tsx | by_app_instance、pcClientOnlineMap、devicesByFloor、isAvailable、楼层展示 |
| 前端 | DeviceSidebar.tsx | useAgentBinding 替代 agent.devices |
| 前端 | api.ts | 移除 devices.list(agentId) |
| Gateway | devices.py | ensure_device_available、_compute_device_available、available 字段、start/stop/status 前校验 |
| Gateway | pc_client.py | vm_status_report 持久化 vm_ids + android_serials 到 devices.pc_client_id |
| Gateway | vm.py | start/stop/status/is_running/get_vnc_status 前 ensure_device_available |
| Gateway | vm_users.py | create/restart/delete 前 ensure_device_available |
| VmControl | cloud_bridge.rs | fetch_running_device_ids 返回 (vm_ids, android_serials)，上报 android_serials |

## 设计要点

- pc_client_id 持久绑定，vm_status_report 只写不清
- device available = pc_client 在线（DeviceRegistry）且 device 运行中
- 前端 isAvailable = pc_client 在 by_app_instance 中且 online
- ensure_device_available: pc_client_id 空→400，pc offline/其他用户→503

## Review 关注点

1. 竞态、边界条件、错误处理
2. 安全：user_id 校验、权限
3. 性能：重复查询、N+1
4. 一致性：前后端语义、API 契约
5. 可维护性：重复代码、导入方式
6. 遗漏：setup 是否需校验、delete 是否需校验
