# Sandbox Service

## 概述与职责

Sandbox Service 是 Novaic 平台的沙箱执行服务，运行在端口 `:19994`，基于 Python / FastAPI 构建。它为 Agent 提供隔离的命令执行环境，确保 Agent 执行的 Shell 命令和文件操作在受控的沙箱空间内完成，不会影响宿主系统。

核心职责包括：

- 在隔离的 Mount Namespace 中执行 Shell 命令
- 管理沙箱的文件系统挂载和隔离
- 提供异步进程执行和输出采集
- 支持沙箱内的文件读写操作

## AsyncProcessRunner 机制

AsyncProcessRunner 是 Sandbox Service 的核心执行引擎，基于 Python 的 `asyncio.subprocess` 实现异步进程管理：

### 生命周期

```
命令请求到达
    ↓
创建 AsyncProcessRunner 实例
    ↓
构造隔离环境（Mount Namespace + Bind Mount）
    ↓
启动子进程（asyncio.create_subprocess_exec）
    ↓
异步采集 stdout / stderr
    ↓
等待进程结束或超时
    ↓
返回执行结果（exit_code, stdout, stderr）
```

### 关键特性

| 特性 | 说明 |
|------|------|
| 异步执行 | 基于 asyncio，不阻塞事件循环，支持并发执行多个命令 |
| 流式输出 | stdout 和 stderr 逐行异步读取，支持实时输出推送 |
| 超时控制 | 可配置命令级超时，超时后发送 SIGTERM → SIGKILL |
| 环境变量 | 支持自定义子进程的环境变量，隔离于宿主环境 |
| 工作目录 | 支持指定子进程的工作目录（在沙箱文件系统内） |

### 错误处理

- **进程超时**：超时后先发送 SIGTERM，等待宽限期后发送 SIGKILL 强制终止。
- **进程崩溃**：捕获非零退出码，将 stderr 输出作为错误信息返回。
- **资源限制**：通过 cgroups 或 ulimit 限制 CPU、内存使用（如已配置）。

## Mount Namespace 隔离

Sandbox Service 利用 Linux Mount Namespace 实现文件系统级别的隔离：

### 隔离原理

```
宿主文件系统
├── /home/user/...       ← 宿主用户目录（沙箱不可见）
├── /var/sandbox/base/   ← 沙箱基础镜像（只读）
└── /var/sandbox/work/   ← 沙箱工作目录（每实例独立）

沙箱视角
├── /                    ← 基础镜像（只读 bind mount）
├── /workspace           ← 工作目录（读写 bind mount）
├── /tmp                 ← 临时目录（tmpfs）
└── /dev, /proc, /sys    ← 最小系统挂载
```

### Bind Mount 命令构造

Sandbox Service 动态构造 Bind Mount 命令，将所需的目录挂载到沙箱内：

1. **基础镜像挂载**：只读挂载基础文件系统，提供基本的 Linux 工具链。
2. **工作目录挂载**：读写挂载用户的工作目录到沙箱的 `/workspace`。
3. **临时目录**：为 `/tmp` 挂载 tmpfs，隔离临时文件。
4. **设备文件**：最小化挂载 `/dev`、`/proc`、`/sys`。

每个沙箱实例拥有独立的 Mount Namespace，互不干扰。沙箱销毁时，所有挂载点自动清理。

### 安全边界

| 安全措施 | 说明 |
|----------|------|
| Mount Namespace | 沙箱只能看到显式挂载的目录 |
| 只读基础镜像 | 防止沙箱修改系统文件 |
| 无网络（可选） | 可配置 Network Namespace 隔离网络 |
| 进程隔离 | 沙箱内的进程不能看到宿主的其他进程 |
| 资源限制 | 通过 cgroups 限制 CPU / 内存 |

## API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/internal/sandbox/execute` | POST | 在沙箱中执行 Shell 命令 |
| `/internal/sandbox/execute/stream` | POST | 流式执行命令（SSE 输出） |
| `/internal/sandbox/file/read` | POST | 读取沙箱内文件内容 |
| `/internal/sandbox/file/write` | POST | 写入文件到沙箱 |
| `/internal/sandbox/file/list` | POST | 列出沙箱内目录内容 |
| `/internal/sandbox/status` | GET | 查询沙箱实例状态 |
| `/internal/sandbox/create` | POST | 创建新的沙箱实例 |
| `/internal/sandbox/destroy` | POST | 销毁沙箱实例 |
| `/health` | GET | 健康检查 |

## 依赖关系

```
Sandbox Service
├── Linux Kernel — Mount Namespace / cgroups 支持
└── 宿主文件系统 — 基础镜像和工作目录
```

Sandbox Service 是底层基础设施服务，不依赖平台内其他服务。它被 Agent Runtime 调用，用于执行 Agent 的 Shell 命令。
