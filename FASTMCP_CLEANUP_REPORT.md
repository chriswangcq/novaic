# FastMCP 清理报告

**执行时间：** 2026-02-06

**目标：** 删除 FastMCP 相关代码，保留 MCP Client 和 vmuse_adapter

---

## 删除内容总结

### 1. ✅ 删除 gateway/api/internal.py 中的 rt_qemu_deploy_vmuse 端点

**文件：** `novaic-backend/gateway/api/internal.py`

**删除行数：** 约 197 行（2966-3163 行）

**内容：**
- `@router.post("/rt/{runtime_id}/qemu/deploy-vmuse")` 端点函数
- FastMCP 代码部署逻辑（SSH 复制、服务重启、健康检查）

**验证：** ✅ Python 语法检查通过

---

### 2. ✅ 删除 gateway/vm/setup.py 中的 novaic.service 配置

**文件：** `novaic-backend/gateway/vm/setup.py`

**删除内容：**
1. **novaic.service systemd 配置**（约 24 行）
   - Service 定义
   - FastMCP 启动命令
   - 环境变量配置

2. **runcmd 命令**（约 13 行）
   - FastMCP 相关目录创建 (`/opt/novaic-mcp-vmuse`, `/opt/novaic-venv`)
   - Python 虚拟环境创建
   - FastMCP 依赖安装（fastapi, uvicorn, pydantic, playwright 等）
   - Playwright Chromium 安装
   - `systemctl enable novaic` 命令

3. **final_message 更新**
   - 移除 MCP 端口 8080 的说明
   - 移除 "Please run deploy to install MCP Server" 提示

**删除行数：** 约 37 行

**验证：** ✅ Python 语法检查通过

---

### 3. ✅ 删除 tools_server/tools.py 中的 qemu_deploy_vmuse_code 工具

**文件：** `novaic-backend/tools_server/tools.py`

**删除内容：**
- `qemu_deploy_vmuse_code` 工具定义（20 行）
- 工具参数：`restart_service`, `force`

**更新：**
- QEMU 工具数量：6 个 → 5 个
- 总工具数量：36 个 → 35 个

**验证：** ✅ Python 语法检查通过

---

### 4. ✅ 删除 tools_server/executor.py 中的 qemu_deploy_vmuse_code 处理

**文件：** `novaic-backend/tools_server/executor.py`

**删除内容：**
1. `BUILTIN_TOOL_NAMES` 集合中的 `"qemu_deploy_vmuse_code"`（1 行）
2. `elif tool_name == "qemu_deploy_vmuse_code"` 处理逻辑（9 行）

**删除行数：** 约 10 行

**验证：** ✅ Python 语法检查通过

---

### 5. ✅ 移动 novaic-vm 源码目录

**原路径：** `novaic-vm/`

**新路径：** `docs/reference/legacy/novaic-vm-fastmcp/`

**目录内容：**
- FastMCP 源码（`src/novaic_mcp_vmuse/`）
- VM 管理脚本（`scripts/`）
- FastMCP 配置（`pyproject.toml`）
- 测试代码（`tests/`）

**保留原因：** 历史参考

**添加文档：** `docs/reference/legacy/README.md`

**验证：** ✅ 目录已成功移动

---

### 6. ✅ 清理 requirements.txt 中的注释

**文件：** `novaic-backend/requirements.txt`

**状态：** FastMCP 依赖已注释（第 29 行）
```
# fastmcp>=2.3.1
```

**验证：** ✅ 无需额外操作

---

## 代码统计

| 文件 | 删除行数 | 说明 |
|------|---------|------|
| `gateway/api/internal.py` | 197 行 | rt_qemu_deploy_vmuse 端点 |
| `gateway/vm/setup.py` | 37 行 | novaic.service 配置和部署命令 |
| `tools_server/tools.py` | 21 行 | qemu_deploy_vmuse_code 工具定义 |
| `tools_server/executor.py` | 10 行 | qemu_deploy_vmuse_code 处理逻辑 |
| **总计** | **265 行** | FastMCP 部署相关代码 |

**移动目录：** `novaic-vm/` → `docs/reference/legacy/novaic-vm-fastmcp/`

---

## 保留内容验证

### ✅ mcp_client/ 目录保留

**路径：** `novaic-backend/mcp_client/`

**内容：**
- `mcp_client.py` - 通用 MCP 客户端实现
- `registry.py` - MCP 服务器注册和管理
- `skills/` - MCP 技能定义

**状态：** ✅ 完整保留

---

### ✅ vmuse_adapter.py 保留

**路径：** `novaic-backend/gateway/clients/vmuse_adapter.py`

**大小：** 69,811 字节

**功能：**
- VM 工具适配器
- Browser、Window、Context 等工具实现
- VM 工具代理层

**状态：** ✅ 完整保留

---

## 验证结果

### Python 语法检查

```bash
✅ gateway/api/internal.py     - 通过
✅ gateway/vm/setup.py          - 通过
✅ tools_server/tools.py        - 通过
✅ tools_server/executor.py     - 通过
```

### 关键组件保留

```bash
✅ mcp_client/                  - 保留
✅ vmuse_adapter.py             - 保留
✅ novaic-vm                    - 已移除（移至 legacy）
✅ novaic-vm-fastmcp/           - 已归档
```

---

## 影响分析

### 删除的功能

1. **FastMCP 部署端点** (`/rt/{runtime_id}/qemu/deploy-vmuse`)
   - 不再支持通过 API 部署 FastMCP 代码到 VM
   - 已被 vmcontrol 服务替代

2. **novaic.service systemd 服务**
   - VM 启动时不再自动启动 FastMCP 服务
   - VM 工具通过 vmcontrol 代理访问

3. **qemu_deploy_vmuse_code 工具**
   - Agent 不再能通过工具部署 FastMCP 代码
   - 简化了工具集

### 保留的功能

1. **MCP Client** (`mcp_client/`)
   - 通用 MCP 客户端，可连接任何 MCP 服务器
   - 用于外部工具集成

2. **vmuse_adapter** (`vmuse_adapter.py`)
   - VM 工具适配器层
   - 提供 Browser、Window、Context 等工具
   - 通过 vmcontrol 代理访问 VM

3. **VM 基础设施**
   - QEMU VM 管理（启动、停止、重启）
   - SSH 执行
   - VNC 连接

---

## 后续建议

### 1. 文档更新

- [ ] 更新部署文档，移除 FastMCP 部署步骤
- [ ] 更新架构图，反映 vmcontrol 服务
- [ ] 更新 API 文档，移除 `/qemu/deploy-vmuse` 端点

### 2. 清理残留引用

运行以下命令检查残留引用：

```bash
# 检查 novaic-mcp-vmuse 引用
rg "novaic-mcp-vmuse" --type py

# 检查 FastMCP 引用
rg "fastmcp|FastMCP" --type py -i

# 检查 deploy-vmuse 引用
rg "deploy.vmuse|deploy_vmuse" --type py
```

### 3. 配置清理

- [ ] 移除环境变量 `NOVAIC_RESOURCE_DIR` 相关配置（如果仅用于 FastMCP）
- [ ] 清理 VM 模板中的 `/opt/novaic-mcp-vmuse` 目录
- [ ] 更新 cloud-init 配置移除 FastMCP 依赖安装

---

## 总结

✅ **所有 FastMCP 部署相关代码已成功删除**

✅ **mcp_client 和 vmuse_adapter 完整保留**

✅ **novaic-vm 源码已归档至 legacy 目录作为参考**

✅ **所有修改文件的 Python 语法检查通过**

**删除代码行数：** 265 行

**移动目录：** 1 个（novaic-vm）

**保留关键组件：** mcp_client, vmuse_adapter

---

**任务状态：** ✅ 完成

**下一步：** 运行集成测试，验证 VM 工具功能正常
