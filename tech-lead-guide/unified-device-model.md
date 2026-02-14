# 统一设备模型设计方案（方案 B）

## 概述

将 LVM 和 AVD 统一为 `devices` 数组，每个设备有统一的公共字段和类型特定字段。

---

## 新数据模型

### 1. 设备基础配置

```python
class DeviceType(str, Enum):
    LINUX = "linux"
    ANDROID = "android"

class DeviceStatus(str, Enum):
    CREATED = "created"      # 配置已创建
    SETUP = "setup"          # 正在初始化
    READY = "ready"          # 就绪（可启动）
    RUNNING = "running"      # 运行中
    STOPPED = "stopped"      # 已停止
    ERROR = "error"          # 错误状态

class DeviceConfig(BaseModel):
    """统一设备配置基类"""
    id: str                           # 设备 ID（UUID）
    type: DeviceType                  # linux / android
    name: str = ""                    # 设备名称（可选）
    created_at: str                   # 创建时间
    status: DeviceStatus = DeviceStatus.CREATED
    
    # 公共资源配置
    memory: int = 4096                # 内存 (MB)
    cpus: int = 4                     # CPU 核心数
    
    # 存储路径（统一管理）
    data_path: str = ""               # 设备数据目录
    
    # 网络配置
    ports: Dict[str, int] = {}        # 端口映射
```

### 2. Linux 设备配置

```python
class LinuxDeviceConfig(DeviceConfig):
    """Linux VM 设备配置"""
    type: DeviceType = DeviceType.LINUX
    
    # Linux 特有字段
    backend: str = "qemu"
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    image_path: str = ""              # 磁盘镜像路径
    cloud_init_complete: bool = False
```

### 3. Android 设备配置

```python
class AndroidDeviceConfig(DeviceConfig):
    """Android 设备配置"""
    type: DeviceType = DeviceType.ANDROID
    
    # Android 特有字段
    avd_name: str = ""                # AVD 名称
    device_serial: str = ""           # 设备序列号
    managed: bool = True              # 是否由 novaic 管理
    system_image: str = ""            # 系统镜像
```

### 4. Agent 配置

```python
class AICAgent(BaseModel):
    """Agent 配置"""
    id: str
    name: str
    created_at: str
    model_id: Optional[str] = None
    
    # 统一设备列表（替代 vm + android）
    devices: List[DeviceConfig] = []
```

---

## 数据库 Schema 变更

### 新增 devices 表

```sql
-- 设备表（替代 vm_config + android_config）
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    type TEXT NOT NULL,               -- 'linux' / 'android'
    name TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'created',
    
    -- 公共资源配置
    memory INTEGER DEFAULT 4096,
    cpus INTEGER DEFAULT 4,
    data_path TEXT DEFAULT '',
    ports TEXT DEFAULT '{}',          -- JSON: {"ssh": 20000, "vmuse": 18000}
    
    -- Linux 特有字段
    backend TEXT DEFAULT 'qemu',
    os_type TEXT DEFAULT 'ubuntu',
    os_version TEXT DEFAULT '24.04',
    image_path TEXT DEFAULT '',
    cloud_init_complete INTEGER DEFAULT 0,
    
    -- Android 特有字段
    avd_name TEXT DEFAULT '',
    device_serial TEXT DEFAULT '',
    managed INTEGER DEFAULT 1,
    system_image TEXT DEFAULT '',
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_devices_agent ON devices(agent_id);
CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(type);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
```

### 简化 agents 表

```sql
-- agents 表移除 vm_config, android_config, ports, setup_complete, cloud_init_complete
ALTER TABLE agents DROP COLUMN vm_config;
ALTER TABLE agents DROP COLUMN android_config;
ALTER TABLE agents DROP COLUMN ports;
ALTER TABLE agents DROP COLUMN setup_complete;
ALTER TABLE agents DROP COLUMN cloud_init_complete;
```

---

## API 变更

### 设备 CRUD API

```
# 设备管理（新增）
POST   /api/agents/{agent_id}/devices           # 添加设备
GET    /api/agents/{agent_id}/devices           # 列出设备
GET    /api/agents/{agent_id}/devices/{id}      # 获取设备
PATCH  /api/agents/{agent_id}/devices/{id}      # 更新设备
DELETE /api/agents/{agent_id}/devices/{id}      # 删除设备

# 设备操作（统一）
POST   /api/devices/{id}/setup                  # 初始化设备
POST   /api/devices/{id}/start                  # 启动设备
POST   /api/devices/{id}/stop                   # 停止设备
GET    /api/devices/{id}/status                 # 设备状态
```

### 废弃的 API

```
# 以下 API 将被废弃
DELETE /api/agents/{id}/vm                      # → DELETE /api/agents/{id}/devices/{device_id}
DELETE /api/agents/{id}/android                 # → DELETE /api/agents/{id}/devices/{device_id}
POST   /api/vm/setup                            # → POST /api/devices/{id}/setup
POST   /api/vm/start                            # → POST /api/devices/{id}/start
POST   /api/vm/stop                             # → POST /api/devices/{id}/stop
POST   /api/vm/android/start                    # → POST /api/devices/{id}/start
POST   /api/vm/android/stop                     # → POST /api/devices/{id}/stop
```

---

## 文件存储结构

```
NOVAIC_DATA_DIR/
└── agents/
    └── {agent_id}/
        └── devices/
            ├── {linux_device_id}/
            │   ├── disk.qcow2
            │   ├── cloud-init.iso
            │   ├── QEMU_EFI.fd
            │   └── QEMU_VARS.fd
            │
            └── {android_device_id}/
                └── {avd_name}.avd/
                    ├── config.ini
                    ├── userdata.img
                    └── ...
```

---

## 数据迁移

### 迁移脚本

```python
def migrate_to_unified_devices(conn):
    """将 vm_config + android_config 迁移到 devices 表"""
    cursor = conn.cursor()
    
    # 获取所有 agents
    cursor.execute("SELECT id, vm_config, android_config, ports FROM agents")
    
    for row in cursor.fetchall():
        agent_id = row[0]
        vm_config = json.loads(row[1] or '{}')
        android_config = json.loads(row[2]) if row[2] else None
        ports = json.loads(row[3] or '{}')
        
        # 迁移 Linux 设备
        if vm_config.get('image_path'):
            device_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO devices (
                    id, agent_id, type, status,
                    memory, cpus, ports, data_path,
                    backend, os_type, os_version, image_path, cloud_init_complete
                ) VALUES (?, ?, 'linux', 'ready', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device_id, agent_id,
                int(vm_config.get('memory', 4096)),
                vm_config.get('cpus', 4),
                json.dumps(ports),
                f"agents/{agent_id}",  # 旧路径
                vm_config.get('backend', 'qemu'),
                vm_config.get('os_type', 'ubuntu'),
                vm_config.get('os_version', '24.04'),
                vm_config.get('image_path', ''),
                1,  # 假设已完成
            ))
        
        # 迁移 Android 设备
        if android_config:
            device_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO devices (
                    id, agent_id, type, status,
                    memory, cpus, ports, data_path,
                    avd_name, device_serial, managed
                ) VALUES (?, ?, 'android', 'ready', ?, ?, ?, ?, ?, ?, ?)
            """, (
                device_id, agent_id,
                4096, 4,  # 默认值
                '{}',
                f"agents/{agent_id}/android",
                android_config.get('avd_name', ''),
                android_config.get('device_serial', ''),
                1 if android_config.get('managed', False) else 0,
            ))
    
    conn.commit()
```

---

## 前端变更

### 类型定义

```typescript
// types/index.ts

type DeviceType = 'linux' | 'android';
type DeviceStatus = 'created' | 'setup' | 'ready' | 'running' | 'stopped' | 'error';

interface DeviceConfig {
  id: string;
  type: DeviceType;
  name: string;
  created_at: string;
  status: DeviceStatus;
  memory: number;
  cpus: number;
  data_path: string;
  ports: Record<string, number>;
}

interface LinuxDevice extends DeviceConfig {
  type: 'linux';
  backend: string;
  os_type: string;
  os_version: string;
  image_path: string;
  cloud_init_complete: boolean;
}

interface AndroidDevice extends DeviceConfig {
  type: 'android';
  avd_name: string;
  device_serial: string;
  managed: boolean;
  system_image: string;
}

type Device = LinuxDevice | AndroidDevice;

interface Agent {
  id: string;
  name: string;
  created_at: string;
  model_id?: string;
  devices: Device[];  // 替代 vm + android
}
```

### API 调用

```typescript
// api.ts

const api = {
  // 设备管理
  devices: {
    list: (agentId: string) => 
      invoke('gateway_get', { path: `/api/agents/${agentId}/devices` }),
    
    create: (agentId: string, device: Partial<Device>) =>
      invoke('gateway_post', { path: `/api/agents/${agentId}/devices`, body: device }),
    
    update: (agentId: string, deviceId: string, updates: Partial<Device>) =>
      invoke('gateway_patch', { path: `/api/agents/${agentId}/devices/${deviceId}`, body: updates }),
    
    delete: (agentId: string, deviceId: string) =>
      invoke('gateway_delete', { path: `/api/agents/${agentId}/devices/${deviceId}` }),
    
    setup: (deviceId: string, options?: any) =>
      invoke('gateway_post', { path: `/api/devices/${deviceId}/setup`, body: options }),
    
    start: (deviceId: string) =>
      invoke('gateway_post', { path: `/api/devices/${deviceId}/start` }),
    
    stop: (deviceId: string) =>
      invoke('gateway_post', { path: `/api/devices/${deviceId}/stop` }),
    
    status: (deviceId: string) =>
      invoke('gateway_get', { path: `/api/devices/${deviceId}/status` }),
  },
};
```

---

## 实施步骤

### 阶段 1：数据库和后端模型

1. 创建 `devices` 表
2. 实现 DeviceConfig, LinuxDeviceConfig, AndroidDeviceConfig 模型
3. 实现 DeviceRepository (CRUD)
4. 数据迁移脚本

### 阶段 2：后端 API

1. 实现 `/api/agents/{id}/devices` CRUD
2. 实现 `/api/devices/{id}/setup|start|stop|status`
3. 修改 VmManager 和 Android 管理逻辑
4. 保留旧 API 作为兼容层（可选）

### 阶段 3：前端

1. 更新类型定义
2. 更新 DeviceSidebar 使用 devices 数组
3. 更新 AddLinuxVMModal / AddAndroidModal
4. 更新 VisualPanel

### 阶段 4：清理

1. 移除 agents 表的 vm_config, android_config 等字段
2. 移除旧 API
3. 更新文档

---

## 验收标准

- [x] Agent 的 devices 数组可以包含多个设备
- [x] Linux 和 Android 设备使用统一的 CRUD API
- [x] 设备文件存储在统一的目录结构下
- [x] 删除设备时同时删除文件
- [x] 前端 DeviceSidebar 正确显示所有设备
- [ ] 旧数据迁移成功（需重启服务验证）

---

## 实施完成记录（2026-02-14）

### 后端实现

| 文件 | 说明 |
|------|------|
| `gateway/db/schema.py` | 添加 devices 表，SCHEMA_VERSION 37→38，迁移函数 |
| `gateway/config/devices.py` | 新增：DeviceType, DeviceStatus, DeviceConfig, LinuxDevice, AndroidDevice |
| `gateway/db/repositories/device.py` | 新增：DeviceRepository CRUD |
| `gateway/api/devices.py` | 新增：统一设备 API（CRUD + setup/start/stop） |
| `gateway/config/agents_db.py` | AICAgent 添加 devices 属性，自动加载设备列表 |
| `main_gateway.py` | 注册设备路由 |

### 前端实现

| 文件 | 说明 |
|------|------|
| `types/index.ts` | 添加 Device 类型、类型守卫函数 |
| `services/api.ts` | 添加 api.devices 命名空间 |
| `components/Layout/DeviceSidebar.tsx` | 使用 agent.devices 和新 API |
| `components/VM/AddLinuxVMModal.tsx` | 使用 api.devices.createLinux/setup/start |
| `components/VM/AddAndroidModal.tsx` | 使用 api.devices.createAndroid/setup/start |
| `components/Visual/VisualPanel.tsx` | 从 agent.devices 获取设备信息 |

### 新 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents/{id}/devices` | 列出设备 |
| POST | `/api/agents/{id}/devices/linux` | 创建 Linux 设备 |
| POST | `/api/agents/{id}/devices/android` | 创建 Android 设备 |
| GET | `/api/agents/{id}/devices/{device_id}` | 获取设备 |
| PATCH | `/api/agents/{id}/devices/{device_id}` | 更新设备 |
| DELETE | `/api/agents/{id}/devices/{device_id}` | 删除设备 |
| POST | `/api/devices/{id}/setup` | 初始化设备 |
| POST | `/api/devices/{id}/start` | 启动设备 |
| POST | `/api/devices/{id}/stop` | 停止设备 |
| GET | `/api/devices/{id}/status` | 设备状态 |
