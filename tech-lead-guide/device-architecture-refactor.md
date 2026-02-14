# 设备架构重构方案

## 概述

本文档描述 NovAIC 项目中 Linux VM (LVM) 和 Android Virtual Device (AVD) 架构的重构方案，目标是简化数据模型、统一 API 路径、实现设备删除功能并清理重复代码。

## 目标

1. **移除 Agent 类型**：改为纯配置驱动
2. **统一数据模型**：合并 VmConfig 定义，规范 android 字段位置
3. **统一 API 路径**：所有设备操作都走 Gateway
4. **实现设备删除**：支持单独移除 VM 或 Android 配置
5. **清理重复代码**：合并 AddAndroidModal

---

## 任务分解

### 任务 1：移除 Agent 类型（后端）

**目标**：Agent 不再有 `agent_type` 字段，改为通过配置判断能力

**涉及文件**：
- `novaic-backend/gateway/config/agents_db.py`
- `novaic-backend/gateway/api/agents.py`
- `novaic-backend/gateway/db/repositories/agent.py`

**改动点**：

1. **`agents_db.py`**：
   ```python
   # 移除 create_agent 中的 agent_type 参数
   # 之前：
   def create_agent(self, name: str, agent_type: str = "linux", ...) -> AICAgent:
   
   # 之后：
   def create_agent(self, name: str, model_id: Optional[str] = None) -> AICAgent:
       """
       创建 Agent，默认无设备配置。
       用户可以后续通过 update_agent 添加 VM 或 Android 配置。
       """
       agent_id = str(uuid.uuid4())
       
       # 创建空的 VM 配置（无 image_path 表示无 VM）
       vm_config = VmConfig()  # 默认 image_path=""
       
       self.repo.create_agent(
           agent_id=agent_id,
           name=name,
           vm_config=vm_config.model_dump(),
           ports={},  # 无端口分配
           model_id=model_id,
       )
       
       return self.get_agent(agent_id)
   ```

2. **`agents.py` API**：
   ```python
   # 简化 CreateAgentRequest
   class CreateAgentRequest(BaseModel):
       name: str
       model: Optional[str] = None  # LLM model ID
       # 移除 agent_type
   
   @router.post("/", response_model=AgentResponse)
   def create_agent(request: CreateAgentRequest):
       manager = get_agent_config_manager()
       agent = manager.create_agent(
           name=request.name,
           model_id=request.model,
       )
       # ... 发送 SYSTEM_WAKE 消息
       return AgentResponse(**agent.model_dump())
   ```

3. **数据库**：
   - `agents` 表的 `vm_config` 字段保持不变
   - 不需要数据库迁移，旧数据仍然兼容

**验收标准**：
- [ ] 创建 Agent 不再需要 `agent_type` 参数
- [ ] 新创建的 Agent 默认无 VM、无 Android
- [ ] 旧 Agent 数据仍然可以正常读取

---

### 任务 2：移除 Agent 类型（前端）

**目标**：前端移除 `AgentType` 类型定义和相关逻辑

**涉及文件**：
- `novaic-app/src/services/api.ts`
- `novaic-app/src/types/index.ts`
- `novaic-app/src/components/Agent/CreateAgentModal.tsx`

**改动点**：

1. **`api.ts`**：
   ```typescript
   // 移除 AgentType
   // 之前：
   export type AgentType = 'chat' | 'linux' | 'android' | 'hybrid';
   
   // 之后：移除此行
   
   // 简化 createAgent 参数
   export async function createAgent(params: { name: string }): Promise<Agent> {
     return invoke('gateway_post', {
       path: '/api/agents',
       body: { name: params.name },
     });
   }
   ```

2. **`CreateAgentModal.tsx`**：
   ```typescript
   // 简化创建逻辑
   const handleSubmit = async () => {
     try {
       const agent = await createAgent({ name: name.trim() });
       onCreated(agent);
       onClose();
     } catch (error) {
       console.error('Failed to create agent:', error);
     }
   };
   ```

3. **`types/index.ts`**：
   - 检查是否有 `AgentType` 相关定义，如有则移除

**验收标准**：
- [ ] 前端创建 Agent 不再传递 `agent_type`
- [ ] TypeScript 编译无错误
- [ ] 创建 Agent 功能正常

---

### 任务 3：统一数据模型

**目标**：
1. 合并 `VmConfig` 定义（目前有两处）
2. 将 `AndroidConfig` 从 `VmConfig.android` 提升为独立字段

**涉及文件**：
- `novaic-backend/gateway/config/agents_db.py`
- `novaic-backend/gateway/vm/manager.py`
- `novaic-backend/gateway/api/agents.py`
- `novaic-backend/gateway/db/repositories/agent.py`
- `novaic-backend/gateway/db/schema.py`

**改动点**：

1. **数据库 schema 变更**（`schema.py`）：
   ```sql
   -- agents 表增加 android_config 字段
   ALTER TABLE agents ADD COLUMN android_config TEXT DEFAULT NULL;
   ```

2. **`agents_db.py`**：
   ```python
   class VmConfig(BaseModel):
       """Linux VM 配置"""
       backend: str = "qemu"
       image_path: str = ""  # 空 = 无 VM
       os_type: str = "ubuntu"
       os_version: str = "24.04"
       memory: str = "4096"
       cpus: int = 4
       ports: PortConfig = Field(default_factory=PortConfig)
       # 移除 android 字段
   
   class AndroidConfig(BaseModel):
       """Android 配置"""
       device_serial: str = ""
       managed: bool = False
       avd_name: Optional[str] = None
   
   class AICAgent(BaseModel):
       """Agent 配置"""
       id: str
       name: str
       created_at: str
       setup_complete: bool = False
       cloud_init_complete: bool = False
       vm: VmConfig = Field(default_factory=VmConfig)
       android: Optional[AndroidConfig] = None  # 独立字段
   ```

3. **`vm/manager.py`**：
   ```python
   # 重命名为 VmRunConfig 以区分
   @dataclass
   class VmRunConfig:
       """VM 运行时配置（非持久化）"""
       agent_id: str
       ports: PortConfig
       memory: str
       cpus: int
       image_path: str
   ```

4. **数据迁移**：
   ```python
   # 在 schema.py 的 migrate_database 中添加
   def migrate_v2_android_config(conn):
       """将 vm_config.android 迁移到独立的 android_config 字段"""
       cursor = conn.cursor()
       cursor.execute("SELECT id, vm_config FROM agents")
       for row in cursor.fetchall():
           agent_id, vm_config_json = row
           if vm_config_json:
               vm_config = json.loads(vm_config_json)
               android = vm_config.pop("android", None)
               if android:
                   cursor.execute(
                       "UPDATE agents SET vm_config = ?, android_config = ? WHERE id = ?",
                       (json.dumps(vm_config), json.dumps(android), agent_id)
                   )
       conn.commit()
   ```

**验收标准**：
- [ ] `VmConfig` 不再包含 `android` 字段
- [ ] `AICAgent` 有独立的 `android` 字段
- [ ] 旧数据迁移成功
- [ ] API 返回的 Agent 结构正确

---

### 任务 4：统一 API 路径

**目标**：所有 Android 操作都走 Gateway，不直连 vmcontrol

**涉及文件**：
- `novaic-app/src/services/android.ts`
- `novaic-app/src/services/api.ts`
- `novaic-app/src/components/VM/AddAndroidModal.tsx`
- `novaic-backend/gateway/api/vm.py`

**当前问题**：
- `DeviceSidebar` 使用 `api.startAndroid()` → Gateway → vmcontrol
- `AddAndroidModal` 使用 `androidService.startEmulator()` → 直连 vmcontrol

**改动点**：

1. **Gateway 增加 Android API**（`vm.py`）：
   ```python
   # 已有的 API（保持不变）
   @router.post("/android/start")
   @router.post("/android/stop")
   
   # 新增 API
   @router.get("/android/devices")
   def list_android_devices():
       """列出所有 Android 设备"""
       # 调用 vmcontrol
   
   @router.get("/android/system-images")
   def list_system_images():
       """列出可用的 Android 系统镜像"""
       # 调用 vmcontrol
   
   @router.post("/android/avd/create")
   def create_avd(request: CreateAvdRequest):
       """创建 AVD"""
       # 调用 vmcontrol
   
   @router.delete("/android/avd/{avd_name}")
   def delete_avd(avd_name: str):
       """删除 AVD"""
       # 调用 vmcontrol
   ```

2. **前端统一使用 api.ts**：
   ```typescript
   // api.ts 新增
   export const android = {
     listDevices: () => invoke('gateway_get', { path: '/api/vm/android/devices' }),
     listSystemImages: () => invoke('gateway_get', { path: '/api/vm/android/system-images' }),
     createAvd: (params) => invoke('gateway_post', { path: '/api/vm/android/avd/create', body: params }),
     deleteAvd: (avdName) => invoke('gateway_delete', { path: `/api/vm/android/avd/${avdName}` }),
     start: (agentId) => invoke('gateway_post', { path: '/api/vm/android/start', body: { agent_id: agentId } }),
     stop: (agentId) => invoke('gateway_post', { path: '/api/vm/android/stop', body: { agent_id: agentId } }),
   };
   ```

3. **修改 AddAndroidModal**：
   ```typescript
   // 之前：
   await androidService.createAvd(avdName, systemImage);
   await androidService.startEmulator(avdName);
   
   // 之后：
   await api.android.createAvd({ avd_name: avdName, system_image: systemImage });
   await api.android.start(currentAgentId);
   ```

4. **保留 androidService.ts**：
   - 仅用于直接与 vmcontrol 通信的场景（如 Scrcpy WebSocket）
   - 或完全移除，所有功能都走 Gateway

**验收标准**：
- [ ] AddAndroidModal 使用 Gateway API
- [ ] DeviceSidebar 使用 Gateway API
- [ ] 所有 Android 操作日志可在 Gateway 中看到
- [ ] vmcontrol 故障时有统一的错误处理

---

### 任务 5：实现设备删除

**目标**：支持单独移除 VM 或 Android 配置

**涉及文件**：
- `novaic-backend/gateway/api/agents.py`
- `novaic-backend/gateway/config/agents_db.py`
- `novaic-app/src/components/Layout/DeviceSidebar.tsx`
- `novaic-app/src/services/api.ts`

**改动点**：

1. **后端 API**（`agents.py`）：
   ```python
   @router.delete("/{agent_id}/vm")
   def remove_vm_config(agent_id: str):
       """移除 Agent 的 Linux VM 配置"""
       manager = get_agent_config_manager()
       
       # 1. 停止 VM（如果运行中）
       vm_manager = get_vm_manager()
       status = vm_manager.get_status(agent_id)
       if status and status.running:
           vm_manager.stop(agent_id)
       
       # 2. 清除 VM 配置
       manager.remove_vm_config(agent_id)
       
       # 3. 可选：删除 VM 文件
       # manager.delete_vm_files(agent_id)
       
       return {"status": "ok", "message": "VM config removed"}
   
   @router.delete("/{agent_id}/android")
   def remove_android_config(agent_id: str):
       """移除 Agent 的 Android 配置"""
       manager = get_agent_config_manager()
       
       # 1. 停止 Android（如果运行中）
       # ...
       
       # 2. 清除 Android 配置
       manager.remove_android_config(agent_id)
       
       # 3. 可选：删除 AVD（如果是托管模式）
       # ...
       
       return {"status": "ok", "message": "Android config removed"}
   ```

2. **后端实现**（`agents_db.py`）：
   ```python
   def remove_vm_config(self, agent_id: str) -> bool:
       """移除 VM 配置"""
       agent = self.get_agent(agent_id)
       if not agent:
           return False
       
       # 重置 VM 配置
       empty_vm = VmConfig()  # image_path=""
       self.repo.update_agent(
           agent_id=agent_id,
           vm_config=empty_vm.model_dump(),
           ports={},
           setup_complete=False,
           cloud_init_complete=False,
       )
       return True
   
   def remove_android_config(self, agent_id: str) -> bool:
       """移除 Android 配置"""
       self.repo.update_agent(
           agent_id=agent_id,
           android_config=None,
       )
       return True
   
   def delete_vm_files(self, agent_id: str):
       """删除 VM 相关文件"""
       vm_dir = self._get_agent_vm_dir(agent_id)
       if vm_dir.exists():
           shutil.rmtree(vm_dir)
   ```

3. **前端 API**（`api.ts`）：
   ```typescript
   export async function removeVmConfig(agentId: string): Promise<void> {
     await invoke('gateway_delete', { path: `/api/agents/${agentId}/vm` });
   }
   
   export async function removeAndroidConfig(agentId: string): Promise<void> {
     await invoke('gateway_delete', { path: `/api/agents/${agentId}/android` });
   }
   ```

4. **前端 UI**（`DeviceSidebar.tsx`）：
   ```typescript
   const handleDeleteDevice = async (device: DeviceInfo) => {
     if (!currentAgentId) return;
     
     try {
       if (device.type === 'linux') {
         await api.removeVmConfig(currentAgentId);
       } else {
         await api.removeAndroidConfig(currentAgentId);
       }
       
       // 刷新 Agent 列表
       await loadAgents();
       
       // 刷新设备状态
       if (device.type === 'linux') {
         await fetchVmStatus();
       } else {
         await fetchAndroidStatus();
       }
     } catch (error) {
       console.error('[DeviceSidebar] Failed to delete device:', error);
     }
   };
   ```

**验收标准**：
- [ ] 可以删除 Linux VM 配置
- [ ] 可以删除 Android 配置
- [ ] 删除后 DeviceSidebar 显示 "+ Linux VM" 或 "+ Android" 按钮
- [ ] 删除前如果设备运行中，先停止

---

### 任务 6：清理重复代码

**目标**：合并 AddAndroidModal，移除重复实现

**涉及文件**：
- `novaic-app/src/components/VM/AddAndroidModal.tsx`（保留）
- `novaic-app/src/components/Android/AddAndroidModal.tsx`（删除）
- 检查其他引用

**改动点**：

1. **检查引用**：
   ```bash
   grep -r "AddAndroidModal" novaic-app/src/
   ```

2. **确认使用的版本**：
   - `DeviceSidebar.tsx` 使用 `../VM/AddAndroidModal`
   - 检查是否有其他地方使用 `../Android/AddAndroidModal`

3. **删除重复文件**：
   ```bash
   rm novaic-app/src/components/Android/AddAndroidModal.tsx
   ```

4. **如果 Android 目录为空，删除目录**：
   ```bash
   rmdir novaic-app/src/components/Android/
   ```

**验收标准**：
- [ ] 只有一个 AddAndroidModal 实现
- [ ] 所有引用都指向正确的文件
- [ ] 功能正常

---

## 执行顺序

建议按以下顺序执行：

1. **任务 6：清理重复代码**（最简单，无风险）
2. **任务 1 + 2：移除 Agent 类型**（前后端一起改）
3. **任务 3：统一数据模型**（需要数据迁移）
4. **任务 4：统一 API 路径**（依赖任务 3）
5. **任务 5：实现设备删除**（依赖任务 3、4）

---

## 测试计划

### 回归测试

每个任务完成后，执行以下测试：

1. **创建 Agent**
   - [ ] 创建新 Agent（无设备）
   - [ ] Agent 列表正确显示

2. **添加 Linux VM**
   - [ ] 点击 "+ Linux VM" 按钮
   - [ ] 选择配置，下载镜像
   - [ ] VM 创建成功
   - [ ] DeviceSidebar 显示 VM 卡片

3. **Linux VM 操作**
   - [ ] 启动 VM
   - [ ] 停止 VM
   - [ ] VNC 显示正常

4. **添加 Android**
   - [ ] 点击 "+ Android" 按钮
   - [ ] 托管模式：创建 AVD
   - [ ] 外部模式：选择设备
   - [ ] DeviceSidebar 显示 Android 卡片

5. **Android 操作**
   - [ ] 启动 Android
   - [ ] 停止 Android
   - [ ] Scrcpy 显示正常

6. **删除设备**
   - [ ] 删除 Linux VM
   - [ ] 删除 Android
   - [ ] 删除后可以重新添加

7. **旧数据兼容**
   - [ ] 旧 Agent 数据正常加载
   - [ ] 旧 Agent 的 VM/Android 功能正常

---

## 风险与注意事项

1. **数据迁移**：任务 3 涉及数据库 schema 变更，需要备份数据
2. **API 兼容**：如果有外部调用 API，需要考虑向后兼容
3. **vmcontrol 依赖**：任务 4 统一 API 后，vmcontrol 故障会影响所有 Android 功能
4. **文件清理**：删除 VM 时是否删除磁盘文件，需要确认用户预期

---

## 时间估计

| 任务 | 预计时间 |
|------|----------|
| 任务 6：清理重复代码 | 0.5h |
| 任务 1：移除 Agent 类型（后端） | 1h |
| 任务 2：移除 Agent 类型（前端） | 0.5h |
| 任务 3：统一数据模型 | 2h |
| 任务 4：统一 API 路径 | 2h |
| 任务 5：实现设备删除 | 1.5h |
| 测试与修复 | 1.5h |
| **总计** | **9h** |

---

## 附录：当前文件结构

```
novaic-backend/
├── gateway/
│   ├── api/
│   │   ├── agents.py          # Agent CRUD API
│   │   └── vm.py              # VM 和 Android API
│   ├── config/
│   │   ├── agents_db.py       # Agent 配置管理（主要）
│   │   └── agents.py          # 导出（可能重复）
│   ├── db/
│   │   ├── repositories/
│   │   │   └── agent.py       # Agent 数据库操作
│   │   └── schema.py          # 数据库表定义
│   └── vm/
│       ├── manager.py         # VM 进程管理
│       ├── repository.py      # vm_processes 表操作
│       └── setup.py           # VM 初始化

novaic-app/
├── src/
│   ├── components/
│   │   ├── Agent/
│   │   │   └── CreateAgentModal.tsx
│   │   ├── Android/
│   │   │   └── AddAndroidModal.tsx  # 重复，待删除
│   │   ├── Layout/
│   │   │   └── DeviceSidebar.tsx
│   │   └── VM/
│   │       ├── AddAndroidModal.tsx  # 保留
│   │       └── AddLinuxVMModal.tsx
│   ├── services/
│   │   ├── api.ts             # Gateway API 封装
│   │   ├── android.ts         # vmcontrol Android API
│   │   └── vm.ts              # VM API 封装
│   └── types/
│       └── index.ts           # 类型定义
```
