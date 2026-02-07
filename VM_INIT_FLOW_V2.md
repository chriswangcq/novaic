# 🔄 VM 初始化流程（V2 - VMUSE 集成版）

## 📋 完整流程概览

```
1. 用户创建 Agent (UI)
   ↓
2. Gateway: 创建 Agent 配置
   ↓
3. Gateway: 分配端口 (SSH + VMUSE)
   ↓
4. Gateway: 下载 Ubuntu 镜像
   ↓
5. Gateway: 创建 VM 磁盘和 cloud-init
   ↓
6. Gateway: 启动 QEMU (带端口转发)
   ↓
7. VM: Ubuntu 启动 + cloud-init 配置
   ↓
8. VM: 安装依赖包
   ↓
9. Gateway: 检测 VM 就绪
   ↓
10. Gateway/Tauri: 部署 VMUSE 服务到 VM
   ↓
11. VM: 启动 VMUSE systemd 服务
   ↓
12. ✅ VM 初始化完成
```

---

## 1️⃣ Agent 创建 (UI → Gateway)

### UI 操作
```typescript
POST /internal/agents
{
  "name": "我的 Agent",
  "model": "anthropic/claude-3-5-sonnet-20241022"
}
```

### Gateway 处理
**文件**: `gateway/api/internal/agents.py`

```python
# 1. 生成 Agent ID
agent_id = str(uuid.uuid4())

# 2. 计算 agent_index (用于端口分配)
agent_index = len(existing_agents)  # 0, 1, 2, ...

# 3. 分配端口
from gateway.config.agents import allocate_ports_for_agent
ports = allocate_ports_for_agent(agent_index)
# 返回: PortConfig(ssh=20000+N, vmuse=18000+N)

# 4. 创建 Agent 配置
agent = AICAgent(
    id=agent_id,
    name=name,
    vm=VmConfig(
        backend="qemu",
        os_type="ubuntu",
        os_version="24.04",
        memory="4096",
        cpus=4,
        ports=ports,  # ← 包含 ssh 和 vmuse 端口
    ),
    setup_complete=False  # ← 需要初始化
)

# 5. 保存到数据库
agent_db.create_agent(agent)
```

**端口分配逻辑**:
```python
# gateway/config/agents.py
BASE_PORT = 20000       # SSH 基础端口
BASE_VMUSE_PORT = 18000 # VMUSE 基础端口

def allocate_ports_for_agent(agent_index: int) -> PortConfig:
    return PortConfig(
        ssh=BASE_PORT + agent_index,      # 20000, 20001, 20002, ...
        vmuse=BASE_VMUSE_PORT + agent_index  # 18000, 18001, 18002, ...
    )
```

---

## 2️⃣ VM 设置 (Gateway → VM Manager)

### 触发方式
- **UI**: 用户点击"设置 VM"按钮
- **API**: `POST /internal/agents/{id}/setup`

### Gateway 处理
**文件**: `gateway/api/internal/agents.py`

```python
async def setup_agent(agent_id: str):
    # 1. 获取 Agent 配置
    agent = agent_db.get_agent(agent_id)
    
    # 2. 检查是否已完成
    if agent.setup_complete:
        return {"status": "already_setup"}
    
    # 3. 下载 Ubuntu 镜像 (如果未下载)
    setup_manager = VmSetupManager(data_dir)
    await setup_manager.download_image(agent.vm.os_type, agent.vm.os_version)
    
    # 4. 创建 VM 磁盘
    vm_manager = get_vm_manager()
    await vm_manager.create_vm_disk(agent_id, agent.vm)
    
    # 5. 标记完成
    agent.setup_complete = True
    agent_db.update_agent(agent)
    
    return {"status": "setup_complete"}
```

### 创建 VM 磁盘流程
**文件**: `gateway/vm/manager.py`

```python
async def create_vm_disk(agent_id: str, vm_config: VmConfig):
    agent_dir = data_dir / "agents" / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 复制 Ubuntu 基础镜像
    base_image = data_dir / "images" / "ubuntu-24.04.qcow2"
    disk_path = agent_dir / "disk.qcow2"
    
    subprocess.run([
        "qemu-img", "create",
        "-f", "qcow2",
        "-F", "qcow2",
        "-b", str(base_image),
        str(disk_path),
        "40G"  # 最大 40GB
    ])
    
    # 2. 生成 SSH 密钥
    ssh_key_manager = get_ssh_key_manager()
    ssh_key_manager.generate_key_for_agent(agent_id)
    
    # 3. 创建 cloud-init ISO (用户数据、网络配置)
    create_cloud_init_iso(agent_id, agent_dir)
    
    # 4. 复制 UEFI 固件 (ARM64)
    if is_arm:
        copy_uefi_firmware(agent_dir)
```

### cloud-init 配置
```yaml
#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - <SSH_PUBLIC_KEY>

chpasswd:
  list: |
    ubuntu:ubuntu
  expire: false

ssh_pwauth: true

packages:
  - xfce4
  - lightdm
  - chromium-browser
  - xdotool
  - scrot
  - wmctrl
  - xclip
  - python3
  - python3-pip
  - curl

runcmd:
  # 创建 VMUSE 安装目录
  - mkdir -p /opt/novaic
  - chown ubuntu:ubuntu /opt/novaic
```

---

## 3️⃣ VM 启动 (Gateway → vmcontrol/QEMU)

### 触发方式
- **UI**: 用户点击"启动 VM"按钮
- **API**: `POST /internal/agents/{id}/vm/start`

### Gateway 处理
**文件**: `gateway/vm/manager.py`

```python
def start(agent_id: str) -> dict:
    # 1. 获取 Agent 配置（包含端口信息）
    agent = agent_db.get_agent(agent_id)
    ports = agent.vm.ports  # PortConfig(ssh=20000, vmuse=18000)
    
    # 2. 检查端口是否被占用
    if _is_port_in_use(ports.ssh):
        raise RuntimeError(f"SSH port {ports.ssh} already in use")
    if _is_port_in_use(ports.vmuse):
        raise RuntimeError(f"VMUSE port {ports.vmuse} already in use")
    
    # 3. 构建 QEMU 命令
    config = VmConfig(
        agent_id=agent_id,
        ports=ports,
        memory="4096",
        cpus=4,
        image_path=str(agent_dir / "disk.qcow2")
    )
    
    qemu_args = _build_qemu_args(config, agent_dir)
    
    # 4. 启动 QEMU 进程
    process = subprocess.Popen(
        [qemu_command] + qemu_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 5. 保存进程信息到数据库
    vm_repo.upsert_process(agent_id, {
        "pid": process.pid,
        "status": "running",
        "started_at": datetime.now().isoformat()
    })
    
    return {"status": "started", "pid": process.pid}
```

### QEMU 启动参数（关键部分）
```python
def _build_qemu_args(config: VmConfig, agent_dir: Path) -> List[str]:
    ports = config.ports
    
    # 端口转发配置 ← 重要！
    port_forward = f"hostfwd=tcp::{ports.ssh}-:22,hostfwd=tcp::{ports.vmuse}-:8080"
    
    args = [
        "-name", f"novaic-vm-{agent_id}",
        "-M", "virt,highmem=on",
        "-cpu", "host",
        "-accel", "hvf",
        "-m", "4096",
        "-smp", "4",
        
        # 网络配置
        "-device", "virtio-net-pci,netdev=net0",
        "-netdev", f"user,id=net0,{port_forward}",  # ← SSH + VMUSE 端口转发
        
        # Guest Agent
        "-chardev", f"socket,path={ga_socket},server=on,wait=off,id=qga0",
        "-device", "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
        
        # 其他配置...
    ]
    
    return args
```

**端口转发效果**:
```
VM:22   → Host:20000  (SSH)
VM:8080 → Host:18000  (VMUSE HTTP API)
```

---

## 4️⃣ VM 启动后初始化 (30-60秒)

### Ubuntu 启动流程
1. **GRUB 引导** (5秒)
2. **内核加载** (10秒)
3. **cloud-init 执行** (20-40秒)
   - 配置用户账户
   - 安装软件包
   - 配置网络
   - 运行自定义命令

### Gateway 检测 VM 就绪
```python
async def wait_for_vm_ready(agent_id: str, timeout: int = 300):
    # 1. 等待 Guest Agent 连接
    for i in range(timeout):
        try:
            client = GuestAgentClient.connect(socket_path)
            await client.ping()
            break
        except:
            await asyncio.sleep(1)
    
    # 2. 等待 SSH 可用
    for i in range(timeout):
        if _is_port_open("localhost", ports.ssh):
            break
        await asyncio.sleep(1)
    
    return True
```

---

## 5️⃣ 部署 VMUSE 服务 (Gateway → VM)

### 部署时机

**选项 A: 自动部署（推荐）**
- VM 启动成功后自动触发
- Gateway 检测到 VM ready 后立即部署

**选项 B: 手动部署**
- UI 提供"部署 VMUSE"按钮
- API: `POST /internal/agents/{id}/vm/deploy-vmuse`

### 部署流程
**文件**: `gateway/vm/vmuse_deployment.py` (需要创建)

```python
async def deploy_vmuse(agent_id: str):
    """
    部署 VMUSE 服务到 VM
    """
    agent = agent_db.get_agent(agent_id)
    ports = agent.vm.ports
    
    # 1. 打包 VMUSE 代码
    vmuse_dir = resource_dir / "novaic-mcp-vmuse"
    tar_path = "/tmp/novaic-mcp-vmuse.tar.gz"
    
    subprocess.run([
        "tar", "czf", tar_path,
        "-C", str(vmuse_dir.parent),
        "novaic-mcp-vmuse"
    ])
    
    # 2. 上传到 VM (通过 SSH)
    ssh_key = ssh_key_manager.get_private_key_path(agent_id)
    subprocess.run([
        "scp",
        "-i", ssh_key,
        "-P", str(ports.ssh),
        "-o", "StrictHostKeyChecking=no",
        tar_path,
        f"ubuntu@localhost:/tmp/"
    ])
    
    # 3. SSH 到 VM 安装
    install_script = """
    cd /opt/novaic
    tar xzf /tmp/novaic-mcp-vmuse.tar.gz
    cd novaic-mcp-vmuse
    
    # 使用清华镜像源安装依赖
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    pip install --break-system-packages -e .
    
    # 创建 systemd 服务
    sudo tee /etc/systemd/system/novaic-vmuse.service > /dev/null <<'UNIT'
[Unit]
Description=NovAIC VMUSE HTTP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/novaic/novaic-mcp-vmuse
Environment="PYTHONPATH=/opt/novaic/novaic-mcp-vmuse/src"
Environment="DISPLAY=:0"
ExecStart=/usr/bin/python3 -m novaic_mcp_vmuse.http_server
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
    
    # 启动服务
    sudo systemctl daemon-reload
    sudo systemctl enable novaic-vmuse
    sudo systemctl start novaic-vmuse
    """
    
    subprocess.run([
        "ssh",
        "-i", ssh_key,
        "-p", str(ports.ssh),
        "-o", "StrictHostKeyChecking=no",
        f"ubuntu@localhost",
        install_script
    ])
    
    # 4. 验证服务启动
    await asyncio.sleep(5)
    health_url = f"http://localhost:{ports.vmuse}/health"
    response = await httpx.get(health_url)
    
    if response.status_code == 200:
        return {"status": "deployed", "health": "ok"}
    else:
        raise RuntimeError("VMUSE service failed to start")
```

---

## 6️⃣ 工具调用流程 (Agent → VM)

### Tools Server 调用
**文件**: `tools_server/executor.py`

```python
async def execute_tool(tool_name: str, arguments: dict):
    # 1. 检查是否是 VM 工具
    if tool_name in VM_TOOL_MAPPING:
        tool, operation = VM_TOOL_MAPPING[tool_name]
        
        # 2. 获取 Agent 的 VMUSE 端口
        agent_response = await httpx.get(
            f"{GATEWAY_URL}/internal/agents/{agent_id}"
        )
        agent_data = agent_response.json()
        vmuse_port = agent_data["vm"]["ports"]["vmuse"]  # 18000
        
        # 3. 直接调用 VM 内的 VMUSE HTTP 服务
        url = f"http://127.0.0.1:{vmuse_port}/api/{tool}/{operation}"
        response = await httpx.post(url, json=arguments)
        
        # 4. 返回原始结果（保留 screenshot 等字段）
        return response.json()
```

### multimodal.py 自动处理图片
**文件**: `task_queue/utils/multimodal.py`

```python
# 检测 screenshot 字段
if "screenshot" in result:
    # 自动转换为 MCP content 格式
    content = [
        {"type": "image", "data": result["screenshot"], "mimeType": "image/png"},
        {"type": "text", "text": f"Width: {result['width']}\nHeight: {result['height']}"}
    ]
```

---

## 7️⃣ 端口使用总览

| Agent Index | SSH Port | VMUSE Port | VM 内服务 |
|------------|----------|------------|----------|
| 0          | 20000    | 18000      | :8080    |
| 1          | 20001    | 18001      | :8080    |
| 2          | 20002    | 18002      | :8080    |
| ...        | ...      | ...        | :8080    |

**说明**:
- VM 内所有 Agent 都监听 8080
- 通过 QEMU 端口转发隔离
- 宿主机通过不同端口访问

---

## 8️⃣ 需要更新的文件清单

### ✅ 已完成
1. `gateway/config/agents.py` - 端口分配
2. `gateway/config/agents_db.py` - 数据模型
3. `gateway/vm/manager.py` - QEMU 启动
4. `tools_server/executor.py` - 工具调用

### 🚧 需要添加
1. **`gateway/vm/vmuse_deployment.py`** - VMUSE 部署逻辑
2. **`gateway/api/internal/agents.py`** - 添加部署 API
3. **UI** - 添加"部署 VMUSE"按钮（可选）

### 🔄 需要集成
1. **VM 启动流程**:
   ```python
   # gateway/vm/manager.py - start()
   # 在 VM 启动成功后添加：
   
   if auto_deploy_vmuse:
       await deploy_vmuse(agent_id)
   ```

2. **Agent 状态跟踪**:
   ```python
   # 添加 vmuse_deployed 字段
   class AICAgent:
       setup_complete: bool = False
       vmuse_deployed: bool = False  # ← 新增
   ```

---

## 9️⃣ 用户体验流程

### 理想流程（全自动）
1. 用户创建 Agent
2. 点击"设置 VM"按钮
3. 等待进度条（2-5分钟）
   - ⏳ 下载镜像
   - ⏳ 创建磁盘
   - ⏳ 启动 VM
   - ⏳ 部署 VMUSE
4. ✅ 显示"VM 已就绪"
5. 开始对话，可以使用 VM 工具

### 手动流程（当前）
1. 用户创建 Agent
2. 点击"设置 VM"
3. 点击"启动 VM"
4. **手动部署 VMUSE**（通过脚本）
5. 开始使用

---

## 🎯 下一步建议

### Priority 1: 自动化部署
创建 `gateway/vm/vmuse_deployment.py`，实现自动部署：
```python
async def deploy_vmuse_to_vm(agent_id: str) -> dict
```

### Priority 2: 状态管理
添加 VM 和 VMUSE 状态跟踪：
```python
class VmStatus:
    running: bool
    vmuse_deployed: bool
    vmuse_healthy: bool
```

### Priority 3: UI 集成
- 显示 VMUSE 部署状态
- 自动重试失败的部署
- 提供手动重新部署选项

---

## 📝 测试检查清单

- [ ] 创建新 Agent，端口正确分配
- [ ] 启动 VM，QEMU 参数包含两个端口转发
- [ ] VM 内 VMUSE 服务监听 8080
- [ ] 宿主机可以访问 `http://localhost:18000/health`
- [ ] Tools Server 可以调用 VM 工具
- [ ] 截图工具返回正确格式（图片可见）
- [ ] 创建第二个 Agent，端口不冲突（18001）

---

Generated: 2026-02-07
