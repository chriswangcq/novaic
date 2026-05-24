# LLM Factory

## 概述与职责

LLM Factory 是 Novaic 平台的大模型调用服务，当前在 API host 上以 Docker 容器运行，监听 `127.0.0.1:19990`，基于 Python / FastAPI 构建。它是一个独立部署的服务，为平台提供统一的 LLM 调用入口，屏蔽不同模型提供商的 API 差异。

核心职责包括：

- 统一的多 Provider 模型调用接口
- API Key 的加密存储和安全管理
- 请求失败时的智能重试策略
- 模型路由和负载分配

## Provider 路由机制

LLM Factory 支持 3 种模型提供商，通过统一接口进行路由和适配：

| Provider | 支持模型 | API 协议 |
|----------|----------|----------|
| OpenAI | GPT-4o, GPT-4, GPT-3.5-Turbo 等 | OpenAI Chat Completions API |
| Anthropic | Claude 4 Opus, Claude 4 Sonnet 等 | Anthropic Messages API |
| Google | Gemini Pro, Gemini Ultra 等 | Google Generative AI API |

### 路由流程

```
调用请求（指定 model_id）
    ↓
查询模型配置 → 确定 Provider 类型
    ↓
选择对应的 Provider 适配器
    ↓
转换请求格式为 Provider 原生格式
    ↓
发送请求到 Provider API
    ↓
转换响应格式为统一格式
    ↓
返回调用方
```

每个 Provider 适配器负责：

- **请求转换**：将统一的请求格式转为 Provider 特定格式（如消息结构、工具定义格式）。
- **响应转换**：将 Provider 响应转为统一格式，包括流式响应的逐块转换。
- **错误映射**：将 Provider 特定错误码映射为统一错误类型。

### 外部默认 URL 配置

LLM Factory 支持通过配置覆盖 Provider 的默认 API 端点，允许接入兼容 API 的第三方服务或自部署模型。

## API Key 加密存储

LLM Factory 采用 RSA-2048 非对称加密方案保护 API Key：

| 组件 | 说明 |
|------|------|
| 加密算法 | RSA-2048 |
| 公钥用途 | 加密 API Key（写入时） |
| 私钥用途 | 解密 API Key（调用时） |
| 存储位置 | SQLite 数据库（密文存储） |
| 密钥管理 | 服务启动时加载密钥对 |

### 存储结构

SQLite 数据库包含 4 张表：

| 表名 | 说明 |
|------|------|
| `providers` | 模型提供商配置（名称、类型、API 端点） |
| `models` | 模型定义（名称、Provider 关联、参数限制） |
| `api_keys` | 加密的 API Key（密文、关联 Provider、创建时间） |
| `usage_logs` | 调用日志（模型、Token 用量、耗时、状态） |

API Key 在写入数据库前使用公钥加密，在发起 LLM 调用时使用私钥解密，确保即使数据库文件泄露，API Key 也无法被直接获取。

## 重试策略

LLM Factory 实现了指数退避重试策略，处理模型 API 的瞬态故障：

```
首次请求失败
    ↓ 等待 base_delay（如 1s）
第 1 次重试
    ↓ 等待 base_delay × 2（如 2s）
第 2 次重试
    ↓ 等待 base_delay × 4（如 4s）
第 3 次重试（最大重试次数）
    ↓ 失败 → 返回错误
```

重试策略的关键参数：

| 参数 | 说明 |
|------|------|
| `max_retries` | 最大重试次数 |
| `base_delay` | 基础等待时间 |
| `max_delay` | 最大等待时间上限 |
| `backoff_factor` | 退避因子（默认 2） |
| `retryable_errors` | 可重试的错误类型（429、500、502、503、504） |

对于 429（Rate Limit）错误，会优先读取响应头中的 `Retry-After` 值作为等待时间。

## API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 统一的模型调用入口（兼容 OpenAI 格式） |
| `/v1/models` | GET | 查询可用模型列表 |
| `/v1/providers` | GET/POST | Provider 配置管理 |
| `/v1/api-keys` | GET/POST/DELETE | API Key 的 CRUD |
| `/health` | GET | 健康检查 |

## 依赖关系

```
LLM Factory
├── OpenAI API      — GPT 系列模型调用
├── Anthropic API   — Claude 系列模型调用
├── Google AI API   — Gemini 系列模型调用
└── SQLite          — 本地持久化（Provider、模型、API Key、日志）
```

LLM Factory 是独立服务，不依赖平台内其他服务。它被 Agent Runtime 和 Cortex 调用。
