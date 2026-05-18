# Blob Service

## 概述与职责

Blob Service 是 Novaic 平台的文件存储服务，运行在端口 `:19995`，基于 Python / FastAPI 构建。它为平台提供统一的二进制数据存储和结构化对象树管理能力，支持本地磁盘和云端 S3 双后端。

核心职责包括：

- 提供 blob:// 协议的原始二进制存储
- 提供结构化的对象树（Object Tree）管理
- 支持本地磁盘和 OSS/S3 双后端存储
- 实现 Multipart 分块上传协议

## 双 API 体系

Blob Service 提供两套独立的 API 体系，分别服务于不同的存储场景：

### blob:// 原始 Blob 存储

面向非结构化的二进制数据存储，适用于图片、截屏、文件附件等场景。

| 特性 | 说明 |
|------|------|
| 寻址方式 | `blob://{blob_id}` URI |
| 数据模型 | 纯二进制数据 + Content-Type 元数据 |
| 操作 | 上传（PUT）、下载（GET）、删除（DELETE） |
| 适用场景 | 截屏图片、文件附件、Agent 生成的媒体文件 |

### Object Tree 结构化对象树

面向层级结构的数据管理，适用于工作空间文件系统、项目目录树等场景。

| 特性 | 说明 |
|------|------|
| 寻址方式 | 路径层级（如 `/workspace/project/src/main.py`） |
| 数据模型 | 树形结构，每个节点可包含数据和子节点 |
| 操作 | 创建节点、读取节点、列出子节点、移动/复制、删除 |
| 适用场景 | 工作空间文件管理、项目结构展示 |

```
双 API 体系

blob:// API                    Object Tree API
┌─────────────┐               ┌──────────────────┐
│ PUT blob    │               │ POST /tree/node  │
│ GET blob    │               │ GET  /tree/node  │
│ DELETE blob │               │ GET  /tree/list  │
└──────┬──────┘               │ PUT  /tree/move  │
       │                      │ DELETE /tree/node│
       │                      └────────┬─────────┘
       └──────────┬───────────────────┘
                  ↓
          统一存储后端层
```

## 存储后端

Blob Service 实现了双后端存储架构，通过统一的后端接口抽象支持本地和云端存储：

### DiskBackend（本地磁盘）

| 属性 | 说明 |
|------|------|
| 存储路径 | 本地文件系统目录（可配置） |
| 文件组织 | 按 blob_id 前缀分桶（如 `ab/cd/abcdef...`） |
| 适用场景 | 本地开发、单机部署 |
| 优势 | 零外部依赖，低延迟 |
| 限制 | 不支持多节点共享，容量受限于磁盘 |

### OssS3Backend（OSS / S3 兼容存储）

| 属性 | 说明 |
|------|------|
| 协议 | S3 兼容 API（支持 AWS S3、阿里云 OSS 等） |
| 认证 | Access Key / Secret Key |
| 适用场景 | 生产环境、多节点部署 |
| 优势 | 无限容量、高可用、多节点共享 |
| 限制 | 需要外部服务依赖，有网络延迟 |

后端选择通过配置决定，两种后端实现相同的存储接口，上层代码无感知。

## Multipart 上传协议

对于大文件，Blob Service 实现了 Multipart 分块上传协议，避免单次请求超时和内存溢出：

### 上传流程

```
客户端                              Blob Service
  │                                      │
  │── POST /blob/upload/init ──────────►│  创建上传会话
  │◄── 返回 upload_id ─────────────────│
  │                                      │
  │── PUT /blob/upload/{id}/part/1 ───►│  上传第 1 块
  │◄── 返回 part ETag ────────────────│
  │                                      │
  │── PUT /blob/upload/{id}/part/2 ───►│  上传第 2 块
  │◄── 返回 part ETag ────────────────│
  │                                      │
  │── ... 重复直到所有块上传完成 ...     │
  │                                      │
  │── POST /blob/upload/{id}/complete ►│  合并所有块
  │◄── 返回 blob_id ──────────────────│
```

### 协议特性

| 特性 | 说明 |
|------|------|
| 分块大小 | 可配置，默认 5MB |
| 并发上传 | 支持多个分块并行上传 |
| 断点续传 | 已上传的分块不需重传 |
| 超时清理 | 未完成的上传会话在超时后自动清理 |

## API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/blob/{blob_id}` | GET | 下载 Blob |
| `/blob` | PUT | 上传 Blob（小文件直传） |
| `/blob/{blob_id}` | DELETE | 删除 Blob |
| `/blob/upload/init` | POST | 初始化 Multipart 上传 |
| `/blob/upload/{id}/part/{n}` | PUT | 上传分块 |
| `/blob/upload/{id}/complete` | POST | 完成 Multipart 上传 |
| `/tree/node` | POST | 创建对象树节点 |
| `/tree/node/{path}` | GET | 读取对象树节点 |
| `/tree/list/{path}` | GET | 列出子节点 |
| `/tree/move` | PUT | 移动/重命名节点 |
| `/tree/node/{path}` | DELETE | 删除节点 |
| `/health` | GET | 健康检查 |

## 依赖关系

```
Blob Service
├── 本地文件系统  — DiskBackend 存储
└── OSS / S3     — OssS3Backend 存储（生产环境）
```

Blob Service 是底层存储服务，不依赖平台内其他服务。它被 Gateway（Blob 代理）、Cortex（载荷外部化）和 Agent Runtime（截屏存储）调用。
