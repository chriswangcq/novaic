# LogicalFS 文件系统抽象

## 概述与职责

LogicalFS 是一个纯 Python 库，**不是独立服务**，不监听任何端口。它为上层（主要是 Cortex）提供统一的文件系统抽象层，将文件操作从具体的存储后端中解耦出来。

```
┌────────────────────┐
│      Cortex        │
│   (调用方/宿主)     │
└────────┬───────────┘
         │  import
┌────────▼───────────┐
│    LogicalFS       │
│   三层抽象架构      │
│                    │
│  ┌──────────────┐  │
│  │   Snapshot   │  │  ← 不可变视图
│  ├──────────────┤  │
│  │  Authority   │  │  ← 可变操作
│  ├──────────────┤  │
│  │    Store     │  │  ← 持久化层
│  └──────┬───────┘  │
└─────────┼──────────┘
          │
┌─────────▼──────────┐
│   Blob Service     │
│  (远端对象存储)     │
└────────────────────┘
```

**核心设计原则：**

- **不可变快照** — 任意时刻的文件系统状态均可通过 Snapshot 冻结，不受后续修改影响
- **读写分离** — 只读操作走 Snapshot，写操作走 Authority，职责清晰
- **存储可插拔** — Store 层可对接不同后端，当前默认实现为 BlobObjectStore

## Snapshot/Authority/Store 抽象

LogicalFS 的核心是三层抽象架构，每一层承担明确的职责：

### Snapshot（快照层）

| 特性 | 说明 |
|-----|------|
| 可变性 | 不可变（immutable） |
| 职责 | 提供某一时刻文件系统的只读视图 |
| 生命周期 | 创建后永远不变，可安全共享和缓存 |
| 典型操作 | 列出目录、读取文件内容、查询文件元信息 |

Snapshot 是一个冻结的文件系统状态。一旦创建，它所呈现的内容不会因为后续的文件修改而变化。这种设计保证了并发场景下的读取一致性。

### Authority（操作层）

| 特性 | 说明 |
|-----|------|
| 可变性 | 可变（mutable） |
| 职责 | 执行文件系统的写操作 |
| 操作类型 | 创建/删除文件、创建/删除目录、写入内容 |
| 快照生成 | 每次修改后可生成新的 Snapshot |

Authority 是唯一允许修改文件系统状态的入口。它管理所有写操作，并在操作完成后能够产出新的不可变 Snapshot。

### Store（持久化层）

| 特性 | 说明 |
|-----|------|
| 职责 | 负责数据的实际持久化 |
| 抽象级别 | 接口层，可对接不同存储后端 |
| 默认实现 | BlobObjectStore（HTTP 适配器） |

Store 层定义了持久化接口，屏蔽了底层存储的具体实现细节。

**三层协作流程：**

```
1. 通过 Authority 执行写操作
   Authority.write_file("/path/to/file", content)
        │
        ▼
2. Authority 委托 Store 持久化数据
   Store.put(key, data)
        │
        ▼
3. 操作完成后生成新 Snapshot
   snapshot = Authority.snapshot()
        │
        ▼
4. 上层通过 Snapshot 读取数据
   snapshot.read_file("/path/to/file")
```

## BlobObjectStore 适配器

BlobObjectStore 是 Store 接口的 HTTP 适配实现，它通过 HTTP 协议与 Blob Service 通信，将文件系统的持久化操作转化为 Blob Service 的 API 调用。

**职责映射：**

| LogicalFS 操作 | Blob Service API | 说明 |
|---------------|-----------------|------|
| 存储文件 | PUT /blobs/:key | 上传文件内容 |
| 读取文件 | GET /blobs/:key | 下载文件内容 |
| 删除文件 | DELETE /blobs/:key | 移除对象 |
| 目录快照 | 组合查询 | 列出指定前缀的所有对象 |

**特性：**

- 基于 HTTP 的异步通信，与 Blob Service 解耦部署
- 支持目录快照（directory snapshot），可获取某个目录下所有文件的不可变视图
- 自动处理二进制与文本内容的序列化

## 使用方式

LogicalFS 作为库被 Cortex 直接引用，无需独立部署或启动。

**典型集成方式：**

```python
from logicalfs import Authority, BlobObjectStore

# 1. 初始化 Store（对接 Blob Service）
store = BlobObjectStore(blob_service_url="http://localhost:8400")

# 2. 创建 Authority（可变操作入口）
authority = Authority(store=store)

# 3. 执行文件操作
await authority.write_file("/workspace/hello.txt", b"Hello World")
await authority.mkdir("/workspace/subdir")

# 4. 生成快照（不可变视图）
snapshot = await authority.snapshot()

# 5. 通过快照读取
content = await snapshot.read_file("/workspace/hello.txt")
files = await snapshot.list_dir("/workspace/")
```

**在 Cortex 中的角色：**

Cortex 使用 LogicalFS 来管理 Agent 的文件工作区。当 Agent 需要读写文件时，Cortex 通过 LogicalFS 的 Authority 执行操作；当需要向 LLM 展示文件系统状态时，通过 Snapshot 获取一致的只读视图。

```
Agent 文件操作请求
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cortex     │────►│  LogicalFS   │────►│ Blob Service │
│  (编排层)    │     │  (抽象层)     │     │  (存储层)     │
└──────────────┘     └──────────────┘     └──────────────┘
```

这种设计使得 Cortex 不需要直接与 Blob Service 打交道，也不需要关心文件存储的具体实现，只需通过 LogicalFS 提供的 Snapshot/Authority 接口即可完成所有文件系统操作。
